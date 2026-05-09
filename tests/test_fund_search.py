from backend.app.services.fund_search import parse_suggestion, search_funds


def test_parse_suggestion_extracts_core_fund_fields():
    item = {
        "CODE": "501018",
        "NAME": "南方原油A",
        "JP": "NFYYA",
        "CATEGORYDESC": "基金",
        "FundBaseInfo": {
            "JJGS": "南方基金",
            "FTYPE": "QDII-商品",
            "DWJZ": 1.821,
            "FSRQ": "2026-05-07",
        },
    }

    result = parse_suggestion(item)

    assert result.code == "501018"
    assert result.name == "南方原油A"
    assert result.pinyin == "NFYYA"
    assert result.company == "南方基金"
    assert result.fund_type == "QDII-商品"
    assert result.latest_net_value == 1.821
    assert result.latest_date == "2026-05-07"


def test_search_funds_limits_and_keeps_only_code_results():
    items = [
        {"CODE": "501018", "NAME": "南方原油A", "CATEGORYDESC": "基金", "FundBaseInfo": {}},
        {"CODE": "00700", "NAME": "腾讯控股", "CATEGORYDESC": "港股", "FundBaseInfo": {}},
        {"CODE": "006476", "NAME": "南方原油C", "CATEGORYDESC": "基金", "FundBaseInfo": {}},
    ]

    results = search_funds("原油", provider=lambda keyword: items, limit=1)

    assert [result.code for result in results] == ["501018"]
