"""Configuração comum dos testes (sem rede, sem segredos reais)."""
import os

os.environ["VTS_DEMO"] = "1"
os.environ["VTS_CACHE_BACKEND"] = "memory"
os.environ["VTS_JWT_SECRET"] = "test-secret-32-bytes-minimum-length-ok"
os.environ["VTS_ADMIN_PASSWORD"] = "test-password-seguro"
