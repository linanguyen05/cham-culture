const express = require('express');
const fs = require('fs/promises');
const bcrypt = require('bcryptjs');
const path = require('path');

const app = express();
const PORT = 3000;
const DATA_PATH = path.join(__dirname, 'data.json');

app.use(express.static(__dirname));
app.use(express.json());

async function readUsers() {
    try {
        const data = await fs.readFile(DATA_PATH, 'utf8');
        const json = JSON.parse(data);
        return json.users || [];
    } catch (error) {
        return [];
    }
}

async function saveUsers(users) {
    let fullData = { users: users };
    try {
        const data = await fs.readFile(DATA_PATH, 'utf8');
        fullData = JSON.parse(data);
        fullData.users = users;
    } catch (e) {}
    await fs.writeFile(DATA_PATH, JSON.stringify(fullData, null, 2), 'utf8');
}

// ĐĂNG KÝ
app.post('/register', async (req, res) => {
    console.log('[REGISTER] Request body:', req.body);
    try {
        const { email, password } = req.body;
        if (!email || !password) {
            return res.status(400).json({ message: 'Thiếu email hoặc mật khẩu' });
        }

        const users = await readUsers();
        if (users.find(u => u.email === email)) {
            console.log('[REGISTER] Email đã tồn tại:', email);
            return res.status(400).json({ message: 'Email này đã tồn tại!' });
        }

        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);
        const nextId = users.length > 0 ? Math.max(...users.map(u => u.id)) + 1 : 1;

        const newUser = {
            id: nextId,
            email: email,
            password: hashedPassword,
            createdAt: new Date().toISOString()
        };

        users.push(newUser);
        await saveUsers(users);
        console.log('[REGISTER] Thành công cho email:', email);
        res.status(201).json({ message: 'Đăng ký thành công!', userId: newUser.id });
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

    const users = await readUsers();
    const user = users.find(u => u.email === email);

    if (!user) {
        console.log('[LOGIN] Không tìm thấy email:', email);
        return res.status(404).json({ message: 'Tài khoản chưa tồn tại, vui lòng đăng ký!' });
    }

    try {
        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            console.log('[LOGIN] Sai mật khẩu cho email:', email);
            return res.status(400).json({ message: 'Mật khẩu không chính xác!' });
        }
        console.log('[LOGIN] Thành công cho email:', email);
        res.status(200).json({ message: 'Đăng nhập thành công! (Trùng khớp dữ liệu)' });
    } catch (err) {
        console.error('[LOGIN] Lỗi bcrypt so sánh hash:', err);
        return res.status(400).json({ message: 'Dữ liệu tài khoản bị lỗi, hãy đăng ký lại!' });
    }
});

app.listen(PORT, () => {
    console.log(`Server đang chạy tại: http://localhost:${PORT}`);
});