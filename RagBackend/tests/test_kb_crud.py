"""
知识库 CRUD 单元测试
pytest 框架测试
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def temp_kb_dir():
    """临时知识库目录 fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def client():
    """FastAPI 测试客户端 fixture"""
    from main import app  # 需要导入实际的 FastAPI 应用

    return TestClient(app)


class TestCreateKnowledgeBase:
    """测试创建知识库"""

    def test_create_kb_success(self, client):
        """测试成功创建知识库"""
        response = client.post(
            "/api/create-knowledgebase/",
            json={"kb_name": "测试知识库", "owner_id": "user123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "000000"
        assert data["message"] == "知识库创建成功"
        assert data["data"]["title"] == "测试知识库"

    def test_create_kb_empty_name(self, client):
        """测试创建空名称知识库"""
        response = client.post(
            "/api/create-knowledgebase/", json={"kb_name": "", "owner_id": "user123"}
        )

        assert response.status_code in [422, 400]

    def test_create_kb_with_path_traversal(self, client):
        """测试防止路径遍历攻击"""
        response = client.post(
            "/api/create-knowledgebase/",
            json={"kb_name": "../../../etc/passwd", "owner_id": "user123"},
        )

        assert response.status_code in [422, 400]

    def test_create_kb_duplicate(self, client):
        """测试创建重复知识库"""
        # 首次创建
        client.post(
            "/api/create-knowledgebase/",
            json={"kb_name": "重复库", "owner_id": "user123"},
        )

        # 再次创建相同名称
        response = client.post(
            "/api/create-knowledgebase/",
            json={"kb_name": "重复库", "owner_id": "user123"},
        )

        assert response.status_code == 409


class TestGetKnowledgeBase:
    """测试获取知识库"""

    def test_get_kb_list_success(self, client):
        """测试获取知识库列表"""
        # 创建两个知识库
        client.post(
            "/api/create-knowledgebase/", json={"kb_name": "kb1", "owner_id": "user1"}
        )
        client.post(
            "/api/create-knowledgebase/", json={"kb_name": "kb2", "owner_id": "user2"}
        )

        response = client.get("/api/get-knowledge-item/")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "000000"
        assert data["total"] >= 2

    def test_get_kb_by_user(self, client):
        """测试按用户过滤知识库"""
        client.post(
            "/api/create-knowledgebase/",
            json={"kb_name": "user1_kb", "owner_id": "user1"},
        )

        response = client.get("/api/get-knowledge-item/?user_id=user1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["owner_id"] == "user1"

    def test_get_kb_not_found(self, client):
        """测试获取不存在的知识库"""
        response = client.get("/api/get-knowledge-item/nonexistent")

        assert response.status_code == 404


class TestUpdateKnowledgeBase:
    """测试更新知识库"""

    def test_update_kb_success(self, client):
        """测试成功更新知识库"""
        # 创建知识库
        client.post(
            "/api/create-knowledgebase/",
            json={"kb_name": "更新测试", "owner_id": "user1"},
        )

        # 更新
        response = client.post(
            "/api/update-knowledgebase-config/更新测试",
            json={
                "title": "更新后的标题",
                "description": "更新后的描述",
                "chunk_size": 2000,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "更新后的标题"
        assert data["data"]["chunk_size"] == 2000


class TestDeleteKnowledgeBase:
    """测试删除知识库"""

    def test_delete_kb_success(self, client):
        """测试成功删除知识库"""
        # 创建知识库
        client.post(
            "/api/create-knowledgebase/",
            json={"kb_name": "删除测试", "owner_id": "user1"},
        )

        # 删除
        response = client.delete("/api/delete-knowledgebase/删除测试")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "000000"

    def test_delete_kb_not_found(self, client):
        """测试删除不存在的知识库"""
        response = client.delete("/api/delete-knowledgebase/nonexistent")

        assert response.status_code == 404


class TestDataValidation:
    """测试数据验证"""

    def test_invalid_chunk_size(self, client):
        """测试无效的 chunk_size"""
        client.post(
            "/api/create-knowledgebase/",
            json={"kb_name": "验证测试", "owner_id": "user1"},
        )

        response = client.post(
            "/api/update-knowledgebase-config/验证测试",
            json={"chunk_size": 50},  # 小于最小值 100
        )

        assert response.status_code in [422, 400]

    def test_invalid_similarity_threshold(self, client):
        """测试无效的相似度阈值"""
        client.post(
            "/api/create-knowledgebase/",
            json={"kb_name": "阈值测试", "owner_id": "user1"},
        )

        response = client.post(
            "/api/update-knowledgebase-config/阈值测试",
            json={"similarity_threshold": 1.5},  # 超出范围 [0, 1]
        )

        assert response.status_code in [422, 400]
