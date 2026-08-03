# ==========================================================
# FOREX RADAR V9 PROFESSIONAL
# MAIN ENGINE (SNIPPET - SIGNAL DEBUG ADDED)
# ==========================================================

# ... (โค้ดส่วนบนคงเดิมทั้งหมด จนถึงลูป for symbol in ... ใน run_scan_cycle)

            for symbol in (
                ["^SET50"]
                +
                STOCKS
                +
                FOREX
            ):
                scan_debug["scan_count"] += 1
                scan_debug["symbols"].append(
                    symbol
                )

                is_stock = (
                    symbol in STOCKS
                    or
                    symbol == "^SET50"
                )

                if (
                    is_stock
                    and
                    not thai_market_open()
                ):
                    continue

                if symbol == "^SET50":
                    df = set50_df
                else:
                    df = get_data(
                        symbol,
                        is_stock,
                        price_cache
                    )

                if df is None:
                    continue
                scan_debug["data_pass"] += 1
                scan_debug["data_symbols"].append(symbol)

                try:
                    signal = analyze_signal(
                        symbol,
                        df
                    )
                except Exception as e:
                    logging.exception(
                        f"SIGNAL ENGINE ERROR {symbol}: {e}"
                    )
                    continue

                if signal is None:
                    continue
                scan_debug["signal_found"] += 1

                score = signal.get(
                    "score",
                    0
                )

                # เพิ่ม Debug แสดงคะแนนและ Trend จริงก่อนเช็คเงื่อนไข Min Score
                logging.info(
                    f"""
SIGNAL DEBUG
Symbol : {symbol}
Trend  : {signal.get('trend')}
Score  : {score}
"""
                )

                minimum = (
                    STOCK_MIN_SCORE
                    if is_stock
                    else FOREX_MIN_SCORE
                )

                if score < minimum:
                    continue
                scan_debug["score_pass"] += 1

                trend = signal.get(
                    "trend",
                    "SIDEWAY"
                )

                if trend not in (
                    "BUY",
                    "SELL"
                ):
                    continue
                scan_debug["trend_pass"] += 1

                # ... (โค้ดส่วนที่เหลือต่อจากนี้คงเดิม)
