def test_saved_group_crud_round_trip(monkeypatch, tmp_path):
    from backend.app.services.saved_groups import (
        create_saved_group,
        delete_saved_group,
        get_saved_group,
        list_saved_groups,
        reset_saved_group_store_for_tests,
        update_saved_group,
    )

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/groups.db")
    reset_saved_group_store_for_tests()

    created = create_saved_group("原油观察组", ["501018", "161129", "501018"])

    assert created.name == "原油观察组"
    assert created.codes == ["501018", "161129"]
    assert created.id

    assert list_saved_groups()[0].id == created.id

    updated = update_saved_group(created.id, "能源观察组", ["501018", "006476"])

    assert updated.name == "能源观察组"
    assert updated.codes == ["501018", "006476"]
    assert get_saved_group(created.id) == updated

    assert delete_saved_group(created.id) is True
    assert get_saved_group(created.id) is None
    assert delete_saved_group(created.id) is False


def test_saved_groups_api_supports_create_update_list_delete(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from backend.app import main
    from backend.app.services.saved_groups import reset_saved_group_store_for_tests

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/api-groups.db")
    reset_saved_group_store_for_tests()

    client = TestClient(main.app)

    create_response = client.post(
        "/api/groups/saved",
        json={"name": "原油观察组", "codes": ["501018", "161129"]},
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["name"] == "原油观察组"
    assert created["codes"] == ["501018", "161129"]

    list_response = client.get("/api/groups/saved")

    assert list_response.status_code == 200
    assert [group["id"] for group in list_response.json()] == [created["id"]]

    update_response = client.put(
        f"/api/groups/saved/{created['id']}",
        json={"name": "能源观察组", "codes": ["501018", "006476"]},
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "能源观察组"
    assert update_response.json()["codes"] == ["501018", "006476"]

    delete_response = client.delete(f"/api/groups/saved/{created['id']}")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True}
    assert client.get("/api/groups/saved").json() == []


def test_saved_group_response_includes_fund_names(monkeypatch, tmp_path):
    from backend.app.services import saved_groups
    from backend.app.services.fund_search import FundSearchResult

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/named-groups.db")
    saved_groups.reset_saved_group_store_for_tests()
    saved_groups.resolve_fund_name.cache_clear()

    def fake_search(keyword: str, limit: int = 10):
        fixtures = {
            "501018": "南方原油A",
            "161129": "易方达原油A人民币",
        }
        return [
            FundSearchResult(
                code=keyword,
                name=fixtures[keyword],
                pinyin=None,
                category=None,
                company=None,
                fund_type=None,
                latest_net_value=None,
                latest_date=None,
            )
        ]

    monkeypatch.setattr(saved_groups, "search_funds", fake_search)

    created = saved_groups.create_saved_group("原油观察组", ["501018", "161129"])

    assert created.funds == [
        saved_groups.SavedFund(code="501018", name="南方原油A"),
        saved_groups.SavedFund(code="161129", name="易方达原油A人民币"),
    ]
