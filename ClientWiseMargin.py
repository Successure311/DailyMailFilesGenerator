INDEX_MARGIN_DATA = {
    "BANKNIFTY": {
        "Expiry": {
            "With_Hedge": 250000,
            "Without_Hedge": 400000
        },
        "Non_Expiry": {
            "With_Hedge": 176000,
            "Without_Hedge": 312000
        }
    },
    "NIFTY": {
        "Expiry": {
            "With_Hedge": 240000,
            "Without_Hedge": 340000
        },
        "Non_Expiry": {
            "With_Hedge": 160000,
            "Without_Hedge": 261000
        }
    },
    "SENSEX": {
        "Expiry": {
            "With_Hedge": 185000,
            "Without_Hedge": 300000
        },
        "Non_Expiry": {
            "With_Hedge": 116000,
            "Without_Hedge": 223000
        }
    }
}

STRATEGY_TRADE_COUNT = {
    "SENSEX": {
        "2T3 TO": 3,
        "DYNAMIC SL": 6,
        "ITM SH": "-",
        "TO": 3
    },
    "BANKNIFTY": {
        "2T3 TO": "-",
        "DYNAMIC SL": 6,
        "ITM SH": "-",
        "TO": "-"
    },
    "NIFTY": {
        "2T3 TO": "-",
        "DYNAMIC SL": 10,
        "ITM SH": 11,
        "TO": 4
    }
}

CLIENT_MARGIN_DATA = [
    {
        "ClientID": "OWN",
        "Code": "H",
        "TotalMargin": 75000000
    },
    {
        "ClientID": "MOSTI23482",
        "Code": "M",
        "TotalMargin": 60000000
    },
    {
        "ClientID": "MOSTI23035",
        "Code": "M",
        "TotalMargin": 70000000
    },
    {
        "ClientID": "SAT2484",
        "Code": "M",
        "TotalMargin": 50000000
    },
    {
        "ClientID": "MOSTI22960",
        "Code": "M",
        "TotalMargin": 20000000
    },
    {
        "ClientID": "MOSTI23372",
        "Code": "K",
        "TotalMargin": 28000000
    },
    {
        "ClientID": "MOSTI23461",
        "Code": "K",
        "TotalMargin": 24000000
    },
    {
        "ClientID": "MOSTI22967",
        "Code": "K",
        "TotalMargin": 18500000
    },
    {
        "ClientID": "MOSTI23395",
        "Code": "K",
        "TotalMargin": 21500000
    },
    {
        "ClientID": "MOSTI22962",
        "Code": "K",
        "TotalMargin": 8500000
    },
    {
        "ClientID": "MOSTI23247",
        "Code": "K",
        "TotalMargin": 16000000
    },
    {
        "ClientID": "H46524",
        "Code": "K",
        "TotalMargin": 9300000
    },
    {
        "Code": "K",
        "ClientID": "MOSTI23422",
        "TotalMargin": 26500000
    }
]

STRATEGY_EXPECTANCY = {
    "BANKNIFTY": {
        "DYNAMIC SL": {
            "Non_Expiry_WOH": 1872000,
            "Non_Expiry_WH": 1056000,
            "Expiry_WOH": 2400000,
            "Expiry_WH": 1500000
        }
    },
    "NIFTY": {
        "DYNAMIC SL": {
            "Non_Expiry_WOH": 2610000,
            "Non_Expiry_WH": 1600000,
            "Expiry_WOH": 3400000,
            "Expiry_WH": 2400000
        },
        "INDEXMOVE": {
            "Non_Expiry_WOH": 520000,
            "Non_Expiry_WH": 320000,
            "Expiry_WOH": 680000,
            "Expiry_WH": 480000
        },
        "ITM SH": {
            "Non_Expiry_WOH": 2871000,
            "Non_Expiry_WH": 1760000,
            "Expiry_WOH": 3740000,
            "Expiry_WH": 2640000
        },
        "TO": {
            "Non_Expiry_WOH": 1044000,
            "Non_Expiry_WH": 640000,
            "Expiry_WOH": 1360000,
            "Expiry_WH": 960000
        }
    },
    "SENSEX": {
        "2T3 TO": {
            "Non_Expiry_WOH": 669000,
            "Non_Expiry_WH": 348000,
            "Expiry_WOH": 900000,
            "Expiry_WH": 555000
        },
        "DYNAMIC SL": {
            "Non_Expiry_WOH": 1338000,
            "Non_Expiry_WH": 696000,
            "Expiry_WOH": 1800000,
            "Expiry_WH": 1110000
        },
        "TO": {
            "Non_Expiry_WOH": 669000,
            "Non_Expiry_WH": 348000,
            "Expiry_WOH": 900000,
            "Expiry_WH": 555000
        }
    }
}