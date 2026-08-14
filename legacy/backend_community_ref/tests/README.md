# Tests

Các test `test_validation_and_service.py`, `test_session.py` và `test_api_contract.py` là unit/contract tests.

Các hành vi SQL-specific như concurrency của `post_likes`, pagination thật và aggregation cần chạy thêm integration test trên một database Supabase test riêng bằng `TEST_DATABASE_URL`; không nên chạy test destructive trên production database.
