# ==========================================================
# DW MESSAGE FORMATTER V9.0 PROFESSIONAL
# Compatible:
# Main.py V8.5
# Signal Engine V8.5
# DW Scanner V9.0
# BLS API V9.7
# ==========================================================


def format_dw_message(
    trend,
    symbol,
    dw,
    market,
    confidence=None,
    price_action=None,
    fibo=None,
    risk="NORMAL",
    target="Standard",
    hold="Intraday",
    quality="B",
    reasons=None
):


    lines = []


    # ======================================================
    # SIGNAL
    # ======================================================

    if trend in ["BUY", "BULLISH"]:

        icon = "🟢"
        signal_text = "BUY"
        dw_type = "CALL"


    elif trend in ["SELL", "BEARISH"]:

        icon = "🔴"
        signal_text = "SELL"
        dw_type = "PUT"


    else:

        icon = "🟡"
        signal_text = "WAIT"
        dw_type = "-"



    # ======================================================
    # HEADER
    # ======================================================

    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("🔥 Forex Radar V9.0")
    lines.append("DW FILTER ALERT")
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("")


    lines.append(
        f"{icon} {symbol}"
    )

    lines.append(
        f"Signal : {signal_text}"
    )

    lines.append(
        f"DW Direction : {dw_type}"
    )

    lines.append(
        f"Market : {market}"
    )

    lines.append("")



    # ======================================================
    # FILTER STATUS
    # ======================================================

    count = 0

    if isinstance(dw, dict):

        count = 1

        dw = [dw]

    elif isinstance(dw, list):

        count = len(dw)



    lines.append(
        "📊 Market Filter"
    )

    lines.append(
        f"Trend : {signal_text}"
    )

    lines.append(
        f"DW Candidates : {count}"
    )


    lines.append("")



    # ======================================================
    # REASONS
    # ======================================================

    if reasons:


        lines.append(
            "🧠 Filter Reasons"
        )


        for r in reasons[:5]:

            lines.append(
                f"✅ {r}"
            )


        lines.append("")



    # ======================================================
    # TRADE MODE
    # ======================================================

    lines.append(
        "⚙ Trade Mode"
    )


    lines.append(
        f"Risk : {risk}"
    )


    lines.append(
        f"Strategy : {target}"
    )


    lines.append(
        f"Holding : {hold}"
    )


    lines.append("")



    # ======================================================
    # FIBONACCI
    # ======================================================

    if isinstance(fibo, dict):


        lines.append(
            "📍 Fibonacci Plan"
        )


        if fibo.get("entry"):

            lines.append(
                f"Entry : {fibo.get('entry')}"
            )


        if fibo.get("stop_loss"):

            lines.append(
                f"Stop Loss : {fibo.get('stop_loss')}"
            )


        if fibo.get("tp1"):

            lines.append(
                f"TP1 : {fibo.get('tp1')}"
            )


        if fibo.get("tp2"):

            lines.append(
                f"TP2 : {fibo.get('tp2')}"
            )


        lines.append("")



    # ======================================================
    # PRICE ACTION
    # ======================================================

    if isinstance(price_action, dict):


        patterns=[]


        mapping = {

            "bullish_engulfing":
            "Bullish Engulfing",

            "bearish_engulfing":
            "Bearish Engulfing",

            "hammer":
            "Hammer",

            "shooting_star":
            "Shooting Star",

            "breakout":
            "Breakout"

        }


        for key,name in mapping.items():

            if price_action.get(key):

                patterns.append(name)



        if patterns:


            lines.append(
                "📈 Price Action"
            )


            for p in patterns:

                lines.append(
                    f"✅ {p}"
                )


            lines.append("")



    # ======================================================
    # DW CANDIDATES
    # ======================================================


    if isinstance(dw, list) and len(dw) > 0:


        lines.append(
            "🎯 DW Candidates (ผ่าน Filter)"
        )


        medals = [

            "🥇",
            "🥈",
            "🥉",
            "4️⃣",
            "5️⃣"

        ]


        for i,item in enumerate(dw[:5]):


            medal = medals[i] if i < len(medals) else "▫️"


            lines.append(
                f"{medal} {item.get('symbol','-')}"
            )


            lines.append(
                f"🏦 Issuer : {item.get('issuer','-')}"
            )


            lines.append(
                f"⚡ Sensitivity : {item.get('sensitivity','-')}"
            )


            lines.append(
                f"Δ Delta : {item.get('delta','-')}"
            )


            lines.append(
                f"🚀 Gearing : {item.get('effective_gearing','-')}"
            )


            lines.append(
                f"↔ Spread : {item.get('spread','-')}"
            )


            lines.append(
                f"📅 Days Left : {item.get('days_left','-')}"
            )


            if item.get("iv"):

                lines.append(
                    f"📊 IV : {item.get('iv')}"
                )


            if item.get("turnover"):

                lines.append(
                    f"💵 Turnover : {item.get('turnover')}"
                )


            lines.append("")



    else:


        lines.append(
            "⚠ No DW Passed Filter"
        )


        lines.append("")



    # ======================================================
    # TRADE PLAN
    # ======================================================


    lines.append(
        "💡 Trade Plan"
    )


    if dw_type == "CALL":


        lines.append(
            "• ใช้ CALL DW ตาม Trend"
        )


        lines.append(
            "• รอจังหวะย่อเข้าแนวรับ"
        )



    elif dw_type == "PUT":


        lines.append(
            "• ใช้ PUT DW ตาม Trend"
        )


        lines.append(
            "• รอเด้งเข้าแนวต้าน"
        )



    else:


        lines.append(
            "• รอสัญญาณใหม่"
        )



    lines.append(
        "• ตัดขาดทุนเมื่อ Trend เปลี่ยน"
    )


    lines.append("")


    lines.append(
        "━━━━━━━━━━━━━━━━━━"
    )


    return "\n".join(lines)