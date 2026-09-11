import os
import requests
import pandas as pd
import numpy as np
import yfinance as yf

# LINE通知設定（GitHub Secretsから自動で読み込まれます）
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.environ.get("LINE_USER_ID")

# 監視する銘柄リスト（例: 米国株や日本株のティッカー。日本株の場合は ".T" をつけます）
# 例: トヨタ自動車(7203.T), Apple(AAPL), Microsoft(MSFT) など
WATCH_LIST = ["7203.T", "9984.T", "AAPL", "TSLA"]

def send_line_message(text):
    """LINEにプッシュ通知を送信する関数"""
    if not CHANNEL_ACCESS_TOKEN or not USER_ID:
        print("LINEの認証情報が設定されていません。")
        return
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": text}]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("LINE通知送信成功:")
    else:
        print(f"LINE通知送信失敗: {response.status_code}, {response.text}")

def calculate_rsi(data, window=14):
    """RSIを計算する関数"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def check_signals():
    """株価データを取得し、売買シグナルを判定する関数"""
    signals = []
    
    for ticker in WATCH_LIST:
        try:
            # 過去半年分のデータを取得
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty or len(df) < 75:
                continue
            
            # カラム名のマルチインデックス対策（yfinanceの仕様変更対策）
            if isinstance(df.columns, pd.MultiIndex):
                df = df.droplevel(1, axis=1)

            # 移動平均線 (SMA 5, 25, 75) の計算
            df['SMA5'] = df['Close'].rolling(window=5).mean()
            df['SMA25'] = df['Close'].rolling(window=25).mean()
            df['SMA75'] = df['Close'].rolling(window=75).mean()
            
            # RSIの計算
            df['RSI'] = calculate_rsi(df['Close'], window=14)
            
            # 最新の数値を取得
            latest = df.iloc[-1]
            close_price = latest['Close']
            sma5 = latest['SMA5']
            sma25 = latest['SMA25']
            sma75 = latest['SMA75']
            rsi = latest['RSI']
            
            # トレンドフォロー＆押し目買い条件:
            # 1. 上昇トレンドのパーフェクトオーダーまたはそれに準ずる形 (SMA5 > SMA25 > SMA75 など、あるいは短期の押し目)
            # 2. RSIが45未満（売られすぎ・押し目）
            # ここではご要望の「SMA 5/25/75 と RSI < 45」の条件を組み込みます
            if sma5 > sma25 and sma25 > sma75 and rsi < 45:
                signal_text = (
                    f"【スイングトレードシグナル検知】\n"
                    f"銘柄: {ticker}\n"
                    f"株価: {close_price:.2f}\n"
                    f"RSI: {rsi:.1f} (売られすぎ圏)\n"
                    f"SMA5: {sma5:.2f} / SMA25: {sma25:.2f} / SMA75: {sma75:.2f}\n"
                    f"👉 押し目買いのチャンスです！"
                )
                signals.append(signal_text)
                
        except Exception as e:
            print(f"{ticker} の処理中にエラーが発生しました: {e}")
            
    return signals

if __name__ == "__main__":
    print("株価チェック処理を開始します...")
    detected_signals = check_signals()
    
    if detected_signals:
        for message in detected_signals:
            send_line_message(message)
        print(f"{len(detected_signals)}件のシグナルをLINEに通知しました。")
    else:
        print("条件に合致する銘柄はありませんでした。")
