# SUPABASE_JWT_SECRET 配置说明

## 🔑 什么是 SUPABASE_JWT_SECRET？

`SUPABASE_JWT_SECRET` 是用于**验证 Supabase 签发的 JWT token** 的密钥。

### 用途

在你的项目中，它用于：

1. **JWT 验证** - 验证前端发送的 Supabase Auth token
2. **用户认证** - 通过 `SupabaseJWTAuthentication` 中间件验证用户身份
3. **自动用户创建** - 根据 JWT 中的 email 自动创建/查找 `UserProfile`

### 代码中的使用

```python
# backend/tradeiq/middleware/supabase_auth.py
# 使用 HS256 算法验证 JWT
payload = jwt.decode(
    token,
    secret,  # 这就是 SUPABASE_JWT_SECRET
    algorithms=["HS256"],
    ...
)
```

## 📍 如何获取 SUPABASE_JWT_SECRET？

### 方法 1: Supabase Dashboard（推荐）

1. 登录 Supabase Dashboard
2. 进入你的项目
3. 导航到：**Settings → API → JWT Settings**
4. 找到 **"JWT Secret"** 或 **"Legacy JWT Secret"**
5. 复制密钥值

**路径：**
```
https://supabase.com/dashboard/project/[YOUR-PROJECT-ID]/settings/api
```

### 方法 2: JWT Keys 页面

1. 导航到：**Settings → JWT Keys**
2. 如果使用旧版（HS256）：
   - 查看 **"Legacy JWT Secret"** 标签页
   - 复制显示的密钥
3. 如果使用新版（ES256）：
   - 需要配置代码使用公钥验证（当前代码使用 HS256）

## ⚠️ 重要说明

### 当前代码使用 HS256（对称加密）

你的代码使用 **HS256** 算法，这是**对称加密**，需要：
- ✅ **JWT Secret**（一个字符串密钥）
- ❌ 不是 Public Key（公钥）

### 图片中的信息

你看到的图片显示的是：
- **Public Key (JWK format)** - 这是**公钥**（用于 ES256 非对称加密）
- **算法：ES256** - 非对称加密算法

**但是：**
- 你的代码使用 **HS256**（对称加密）
- 需要的是 **JWT Secret**（字符串），不是公钥

### Supabase 的密钥类型

Supabase 支持两种 JWT 签名方式：

| 类型 | 算法 | 密钥格式 | 用途 |
|------|------|---------|------|
| **Legacy** | HS256 | 字符串密钥 | 对称加密，需要 JWT Secret |
| **New** | ES256 | 公钥/私钥对 | 非对称加密，需要 Public Key |

**你的项目使用 Legacy HS256**，所以需要 JWT Secret 字符串。

## 🔧 配置步骤

### 1. 获取 JWT Secret

在 Supabase Dashboard：
1. Settings → API
2. 找到 **"JWT Secret"** 或 **"Legacy JWT Secret"**
3. 点击 "Reveal" 或 "Show" 显示密钥
4. 复制完整的密钥字符串

### 2. 添加到 .env

```bash
# Supabase Auth (Phase 6) - Get from Supabase Dashboard -> Settings -> API -> JWT Secret
SUPABASE_JWT_SECRET=your-jwt-secret-string-here
SUPABASE_URL=https://omwlpupmmdgppvsmhugl.supabase.co
```

### 3. 验证配置

```bash
cd backend
python manage.py shell
```

```python
from django.conf import settings
print(settings.SUPABASE_JWT_SECRET)  # 应该显示你的密钥
```

## 🎯 是否需要配置？

### ✅ 需要配置的情况

- 前端使用 Supabase Auth（Google Sign-In 等）
- API 需要验证 JWT token
- 需要用户认证功能

### ❌ 不需要配置的情况

- 只是 demo，不需要真实用户认证
- 使用 mock 数据，不连接前端
- 只测试后端功能

## 📝 注意事项

1. **安全性**：
   - JWT Secret 是敏感信息，不要提交到 Git
   - 已在 `.gitignore` 中忽略 `.env` 文件

2. **密钥格式**：
   - JWT Secret 是一个**长字符串**（通常 32+ 字符）
   - 不是 JSON 格式
   - 不是 Public Key

3. **算法匹配**：
   - 确保 Supabase 项目使用 HS256（Legacy）
   - 如果项目已升级到 ES256，需要修改代码使用公钥验证

## 🔍 如何确认项目使用哪种算法？

在 Supabase Dashboard：
1. Settings → JWT Keys
2. 查看显示的密钥类型：
   - 如果看到 "Legacy JWT Secret" → 使用 HS256 ✅
   - 如果只看到 Public Key (JWK) → 使用 ES256 ⚠️

## 💡 如果项目使用 ES256（新版本）

如果你的 Supabase 项目已升级到 ES256，需要修改代码：

1. 使用 Public Key 而不是 Secret
2. 修改算法为 ES256
3. 使用 JWKS URL 获取公钥

但这需要代码修改，当前代码是为 HS256 设计的。

## ✅ 总结

- **SUPABASE_JWT_SECRET** = Supabase Dashboard → Settings → API → JWT Secret
- 是一个**字符串密钥**（不是公钥）
- 用于验证 Supabase 签发的 JWT token
- 如果不需要用户认证，可以暂时不配置
