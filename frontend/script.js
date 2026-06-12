const express = require('express');
const fs = require('fs/promises');
const bcrypt = require('bcryptjs');
const path = require('path');
const sqlite3 = require('sqlite3');
const { open } = require('sqlite');

const app = express();
const PORT = 3000;
const DATA_PATH = path.join(__dirname, 'data.json');
const DB_PATH = path.join(__dirname, 'cham_culture.db');

app.use(express.static(__dirname));
app.use(express.json());

let db;

// Hàm tạo username đẹp từ email
function generateUsernameFromEmail(email) {
    const part = email.split('@')[0];
    return part.split(/[\._-]/).map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

// Khởi tạo SQLite Database và tạo các bảng theo schema yêu cầu
async function initDB() {
    db = await open({
        filename: DB_PATH,
        driver: sqlite3.Database
    });

    // Kích hoạt khóa ngoại trong SQLite
    await db.run('PRAGMA foreign_keys = ON;');

    // 1. BẢNG TÀI KHOẢN (Users)
    await db.run(`
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            username TEXT NOT NULL,
            avatar_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    `);

    // 2. BẢNG BÀI ĐĂNG (Posts)
    await db.run(`
        CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT, -- Lưu dưới dạng JSON string để chứa danh sách ảnh
            tag TEXT CHECK(tag IN ('Văn hóa', 'Ẩm thực', 'Daily', 'Trải nghiệm', 'Hỏi đáp', 'Lễ hội')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    `);

    // 3. BẢNG LƯỢT LIKE (Likes)
    await db.run(`
        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER,
            post_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, post_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
        );
    `);

    // 4. BẢNG BÌNH LUẬN (Comments)
    await db.run(`
        CREATE TABLE IF NOT EXISTS comments (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    `);

    // Kiểm tra xem database đã có dữ liệu chưa. Nếu chưa, migrate từ data.json hoặc chèn mock data.
    const userCount = await db.get('SELECT COUNT(*) as count FROM users');
    if (userCount.count === 0) {
        let migrated = false;
        
        // Cố gắng migrate từ file data.json cũ để bảo toàn tài khoản của người dùng
        try {
            const dataExists = await fs.access(DATA_PATH).then(() => true).catch(() => false);
            if (dataExists) {
                const data = await fs.readFile(DATA_PATH, 'utf8');
                const json = JSON.parse(data);
                if (json.users && json.users.length > 0) {
                    console.log(`[DB INIT] Phát hiện và đang migrate ${json.users.length} tài khoản từ data.json...`);
                    for (const user of json.users) {
                        const generatedUsername = generateUsernameFromEmail(user.email);
                        const defaultAvatar = `https://i.pravatar.cc/150?img=${Math.floor(Math.random() * 70) + 1}`;
                        await db.run(
                            'INSERT OR IGNORE INTO users (email, password, username, avatar_url, created_at) VALUES (?, ?, ?, ?, ?)',
                            [user.email, user.password, generatedUsername, defaultAvatar, user.createdAt || new Date().toISOString()]
                        );
                    }
                    migrated = true;
                }
            }
        } catch (e) {
            console.log('[DB INIT] Không thể migrate từ data.json:', e.message);
        }

        // Nếu vẫn trống (hoặc không migrate được gì), tiến hành chèn dữ liệu mẫu (Mock data)
        const checkUsers = await db.get('SELECT COUNT(*) as count FROM users');
        if (checkUsers.count === 0) {
            console.log('[DB INIT] Đang chèn tài khoản mock data...');
            await db.run(
                'INSERT INTO users (email, password, username, avatar_url) VALUES (?, ?, ?, ?)',
                [
                    'minhanh@gmail.com',
                    '$2b$12$ExampleHashedPassword8CharactersLong...', // Mật khẩu hash giả lập
                    'Minh Anh',
                    'uploads/avatars/7692.jpg'
                ]
            );
        }

        // Chèn bài đăng mock data
        const checkPosts = await db.get('SELECT COUNT(*) as count FROM posts');
        if (checkPosts.count === 0) {
            console.log('[DB INIT] Đang chèn bài đăng mock data...');
            const firstUser = await db.get('SELECT user_id FROM users LIMIT 1');
            if (firstUser) {
                await db.run(
                    'INSERT INTO posts (user_id, content, image_url, tag) VALUES (?, ?, ?, ?)',
                    [
                        firstUser.user_id,
                        'Hi',
                        '["uploads/posts/travel_01.jpg", "uploads/posts/travel_02.jpg"]',
                        'Trải nghiệm'
                    ]
                );
            }
        }
    }
}

// Hàm chuyển đổi tab từ Frontend thành tag tương ứng trong SQLite (đảm bảo không vi phạm CHECK constraint)
function mapTabToTag(tab) {
    const mappings = {
        "Văn hóa": "Văn hóa",
        "Ẩm thực": "Ẩm thực",
        "Câu hỏi": "Hỏi đáp",
        "Trải nghiệm": "Trải nghiệm",
        "Lễ hội": "Lễ hội",
        "Daily": "Daily"
    };
    return mappings[tab] || null;
}

// Hàm chuyển đổi topic được chọn ở modal đăng bài thành tag tương ứng
function mapTopicToTag(topic) {
    const mappings = {
        "Văn hóa Chăm": "Văn hóa",
        "Ẩm thực Chăm": "Ẩm thực",
        "Daily": "Daily",
        "Du lịch – Trải nghiệm": "Trải nghiệm",
        "Hỏi đáp": "Hỏi đáp",
        "Lễ hội": "Lễ hội"
    };
    return mappings[topic] || "Daily";
}

// Hàm tính khoảng thời gian tương đối chuyên nghiệp
function getRelativeTime(timestamp) {
    if (!timestamp) return 'Vừa xong';
    const now = new Date();
    let dateStr = timestamp;
    // SQLite TIMESTAMP mặc định lưu giờ UTC không có hậu tố Z. Ta chuẩn hóa để JS nhận diện đúng UTC.
    if (typeof timestamp === 'string' && !timestamp.endsWith('Z') && !timestamp.includes('+')) {
        dateStr = timestamp.replace(' ', 'T') + 'Z';
    }
    const date = new Date(dateStr);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    return `${diffDays} ngày trước`;
}

// =========================================================================
// CÁC API AUTHENTICATION (ĐÃ CHUYỂN SANG SQLITE)
// =========================================================================

// ĐĂNG KÝ
app.post('/register', async (req, res) => {
    console.log('[REGISTER] Request body:', req.body);
    try {
        const { email, password } = req.body;
        if (!email || !password) {
            return res.status(400).json({ message: 'Thiếu email hoặc mật khẩu' });
        }

        // Kiểm tra email trùng lặp trong SQLite
        const existingUser = await db.get('SELECT * FROM users WHERE email = ?', [email]);
        if (existingUser) {
            console.log('[REGISTER] Email đã tồn tại:', email);
            return res.status(400).json({ message: 'Email này đã tồn tại!' });
        }

        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);
        const username = generateUsernameFromEmail(email);
        const avatarUrl = `https://i.pravatar.cc/150?img=${Math.floor(Math.random() * 70) + 1}`;

        const result = await db.run(
            'INSERT INTO users (email, password, username, avatar_url) VALUES (?, ?, ?, ?)',
            [email, hashedPassword, username, avatarUrl]
        );

        console.log('[REGISTER] Đăng ký thành công cho email:', email);
        res.status(201).json({ 
            message: 'Đăng ký thành công!', 
            userId: result.lastID,
            user: {
                username,
                avatar_url: avatarUrl
            }
        });
    } catch (error) {
        console.error('[REGISTER] Lỗi server:', error);
        res.status(500).json({ message: 'Lỗi server!' });
    }
});

// ĐĂNG NHẬP
app.post('/login', async (req, res) => {
    console.log('[LOGIN] Request body:', req.body);
    const { email, password } = req.body;
    if (!email || !password) {
        return res.status(400).json({ message: 'Thiếu email hoặc mật khẩu' });
    }

    try {
        // Tìm tài khoản trong SQLite
        const user = await db.get('SELECT * FROM users WHERE email = ?', [email]);
        if (!user) {
            console.log('[LOGIN] Không tìm thấy email:', email);
            return res.status(404).json({ message: 'Tài khoản chưa tồn tại, vui lòng đăng ký!' });
        }

        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            console.log('[LOGIN] Mật khẩu sai cho email:', email);
            return res.status(400).json({ message: 'Mật khẩu không chính xác!' });
        }

        console.log('[LOGIN] Đăng nhập thành công:', email);
        res.status(200).json({ 
            message: 'Đăng nhập thành công!',
            user: {
                user_id: user.user_id,
                email: user.email,
                username: user.username,
                avatar_url: user.avatar_url
            }
        });
    } catch (err) {
        console.error('[LOGIN] Lỗi server khi kiểm tra đăng nhập:', err);
        res.status(500).json({ message: 'Lỗi hệ thống!' });
    }
});

// =========================================================================
// CÁC API CỘNG ĐỒNG (THAY THẾ FLASK BACKEND BẰNG SQLITE)
// =========================================================================

// API 1: LẤY THÔNG TIN NGƯỜI DÙNG VỪA ĐĂNG NHẬP / ĐĂNG KÝ
app.get('/api/current-user', async (req, res) => {
    try {
        // Lấy tài khoản được thêm vào cơ sở dữ liệu gần nhất để hiển thị
        const user = await db.get('SELECT username, avatar_url FROM users ORDER BY user_id DESC LIMIT 1');
        if (user) {
            return res.status(200).json({
                success: true,
                data: {
                    name: user.username,
                    avatar: user.avatar_url || "https://i.pravatar.cc/150?img=47"
                }
            });
        }
        
        // Phương án dự phòng (Fallback) nếu chưa có user nào trong DB
        res.status(200).json({
            success: true,
            data: {
                name: "Lan Nhi",
                avatar: "https://i.pravatar.cc/150?img=47"
            }
        });
    } catch (error) {
        console.error('[GET CURRENT USER] Lỗi:', error);
        res.status(500).json({ success: false, message: 'Lỗi xử lý định danh tài khoản!', error: error.message });
    }
});

// API 2: LẤY DANH SÁCH BÀI VIẾT FEED (DÙNG SQL JOIN & SUBQUERY TÍNH LIKE/COMMENT)
app.get('/api/posts', async (req, res) => {
    try {
        const tabName = req.query.tab || 'Tổng quan';
        
        let query = `
            SELECT 
                p.post_id AS id,
                u.username AS authorName,
                u.avatar_url AS authorAvatar,
                p.created_at AS createdAt,
                p.tag AS category,
                p.content AS text,
                p.image_url AS images,
                (SELECT COUNT(*) FROM likes l WHERE l.post_id = p.post_id) AS likes,
                (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.post_id) AS comments
            FROM posts p
            LEFT JOIN users u ON p.user_id = u.user_id
        `;
        
        let params = [];
        
        if (tabName === 'Tổng quan' || !tabName) {
            query += ' ORDER BY p.post_id DESC';
        } else if (tabName === 'Được quan tâm') {
            // Sắp xếp bài viết được nhiều like nhất lên đầu
            query += ' ORDER BY likes DESC, p.post_id DESC';
        } else {
            const mappedTag = mapTabToTag(tabName);
            if (mappedTag) {
                query += ' WHERE p.tag = ? ORDER BY p.post_id DESC';
                params.push(mappedTag);
            } else {
                query += ' ORDER BY p.post_id DESC';
            }
        }
        
        const rows = await db.all(query, params);
        
        const postsList = rows.map(row => {
            let parsedImages = [];
            try {
                if (row.images) {
                    parsedImages = JSON.parse(row.images);
                }
            } catch (e) {
                console.error('Không thể parse JSON mảng ảnh bài viết:', row.images, e);
            }
            
            // Map tag DB về dạng hiển thị đẹp mắt trên Frontend
            let displayCategory = row.category;
            if (row.category === 'Văn hóa') displayCategory = 'Văn hóa Chăm';
            else if (row.category === 'Ẩm thực') displayCategory = 'Ẩm thực Chăm';
            else if (row.category === 'Trải nghiệm') displayCategory = 'Du lịch – Trải nghiệm';
            
            return {
                id: row.id,
                authorName: row.authorName || 'Ẩn danh',
                authorAvatar: row.authorAvatar || 'https://i.pravatar.cc/150?img=47',
                timeText: getRelativeTime(row.createdAt),
                category: displayCategory,
                text: row.text,
                images: parsedImages,
                likes: row.likes || 0,
                comments: row.comments || 0
            };
        });
        
        res.status(200).json({ success: true, count: postsList.length, data: postsList });
    } catch (error) {
        console.error('[GET POSTS] Lỗi:', error);
        res.status(500).json({ success: false, message: 'Lỗi lấy dữ liệu bài viết!', error: error.message });
    }
});

// API 3: LƯU BÀI VIẾT MỚI (LIÊN KẾT NGOẠI KHÓA VỚI USER_ID CỦA NGƯỜI DÙNG)
app.post('/api/posts', async (req, res) => {
    try {
        const data = req.body;
        if (!data) {
            return res.status(400).json({ success: false, message: 'Dữ liệu trống!' });
        }
        
        const { authorName, category, text, images } = data;
        if (!text && (!images || images.length === 0)) {
            return res.status(400).json({ success: false, message: 'Nội dung bài viết rỗng!' });
        }
        
        // Tìm user_id tương ứng với username gửi từ client
        let user = await db.get('SELECT user_id FROM users WHERE username = ?', [authorName]);
        if (!user) {
            // Fallback lấy tài khoản đăng ký cuối cùng
            user = await db.get('SELECT user_id FROM users ORDER BY user_id DESC LIMIT 1');
        }
        
        if (!user) {
            return res.status(400).json({ success: false, message: 'Người dùng không hợp lệ!' });
        }
        
        const mappedTag = mapTopicToTag(category);
        const imagesJson = JSON.stringify(images || []);
        
        await db.run(
            'INSERT INTO posts (user_id, content, image_url, tag) VALUES (?, ?, ?, ?)',
            [user.user_id, text || '', imagesJson, mappedTag]
        );
        
        res.status(201).json({ success: true, message: 'Đăng bài thành công!' });
    } catch (error) {
        console.error('[CREATE POST] Lỗi:', error);
        res.status(500).json({ success: false, message: 'Lỗi ghi nhận bài viết!', error: error.message });
    }
});

// API 4: BẢNG XẾP HẠNG CHỦ ĐỀ SIDEBAR ĐỘNG
app.get('/api/topics-count', async (req, res) => {
    try {
        const defaultTopics = {
            "Hỏi đáp": 42,
            "Lễ hội Katê": 36,
            "Văn hóa Chăm": 28,
            "Du lịch – Trải nghiệm": 18,
            "Ẩm thực Chăm": 15,
            "Kinh nghiệm": 0
        };
        
        // Đếm số lượng bài viết của từng tag trong database
        const rows = await db.all('SELECT tag, COUNT(*) as count FROM posts GROUP BY tag');
        
        const dbCounts = {};
        rows.forEach(row => {
            let topicName = row.tag;
            if (row.tag === 'Văn hóa') topicName = 'Văn hóa Chăm';
            else if (row.tag === 'Ẩm thực') topicName = 'Ẩm thực Chăm';
            else if (row.tag === 'Trải nghiệm') topicName = 'Du lịch – Trải nghiệm';
            else if (row.tag === 'Lễ hội') topicName = 'Lễ hội Katê';
            
            dbCounts[topicName] = (dbCounts[topicName] || 0) + row.count;
        });
        
        // Cộng dồn với dữ liệu mặc định để hiển thị phong phú hơn
        const responseData = Object.keys(defaultTopics).map(name => {
            return {
                name: name,
                count: defaultTopics[name] + (dbCounts[name] || 0)
            };
        });
        
        responseData.sort((a, b) => b.count - a.count);
        
        res.status(200).json({ success: true, data: responseData });
    } catch (error) {
        console.error('[TOPICS COUNT] Lỗi:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// API 5: THÀNH VIÊN TÍCH CỰC TOP 1 (JOIN ĐỂ LẤY THÔNG TIN CHI TIẾT USER)
app.get('/api/active-member', async (req, res) => {
    try {
        const row = await db.get(`
            SELECT 
                u.username AS name,
                u.avatar_url AS avatar,
                COUNT(*) as postCount
            FROM posts p
            JOIN users u ON p.user_id = u.user_id
            GROUP BY p.user_id
            ORDER BY postCount DESC
            LIMIT 1
        `);
        
        let memberData;
        if (row) {
            memberData = {
                name: row.name,
                avatar: row.avatar || "https://i.pravatar.cc/150?img=47",
                postCount: row.postCount
            };
        } else {
            memberData = {
                name: "Chưa có dữ liệu",
                avatar: "https://i.pravatar.cc/150?img=47",
                postCount: 0
            };
        }
        
        res.status(200).json({ success: true, data: memberData });
    } catch (error) {
        console.error('[ACTIVE MEMBER] Lỗi:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Khởi động Database rồi mới lắng nghe kết nối từ Client
initDB().then(() => {
    app.listen(PORT, () => {
        console.log(`Server đang chạy tại: http://localhost:${PORT}`);
    });
}).catch(err => {
    console.error('Không thể khởi tạo cơ sở dữ liệu SQLite:', err);
});