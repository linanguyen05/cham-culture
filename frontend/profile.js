// Hiển thị trước ảnh avatar khi ng dùng vừa chọn file xong
const avatarInput = document.getElementById('avatar');
const previewImage = document.getElementById('preview-avatar');

avatarInput.addEventListener('change', function() {
    const file = this.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
        }
        reader.readAsDataURL(file);
    }
});

// Xử lý gửi form bằng AJAX
document.getElementById('profileForm').addEventListener('submit', function(e) {
    e.preventDefault(); 
    
    let formData = new FormData(this);
    
    // Lấy ID người dùng tạm thời từ localStorage (lưu sau khi đăng ký thành công)
    const tempUserId = localStorage.getItem('tempUserId');
    if (tempUserId) {
        formData.append('userId', tempUserId);
    } else {
        // Dự phòng nếu người dùng đã đăng nhập trước đó và muốn cập nhật profile
        const loggedInUser = localStorage.getItem('loggedInUser');
        if (loggedInUser) {
            try {
                const userObj = JSON.parse(loggedInUser);
                if (userObj.user_id) {
                    formData.append('userId', userObj.user_id);
                }
            } catch(err) {
                console.error("Lỗi đọc session người dùng:", err);
            }
        }
    }

    const statusMsg = document.getElementById('status-msg');
    statusMsg.style.display = 'block';
    statusMsg.style.color = 'blue';
    statusMsg.innerText = 'Đang lưu thông tin...';

    fetch('/update_profile', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err; });
        }
        return response.json();
    })
    .then(data => {
        statusMsg.style.display = 'block';
        if(data.message) {
            statusMsg.style.color = 'green';
            statusMsg.innerText = data.message;
            
            // Cập nhật thông tin lưu tại client
            if (data.user) {
                localStorage.setItem('loggedInUser', JSON.stringify({
                    user_id: data.user.user_id,
                    name: data.user.username,
                    avatar: data.user.avatar_url || "avatarmacdinh.svg"
                }));
            }
            
            // Xóa ID tạm thời
            localStorage.removeItem('tempUserId');

            // Chuyển hướng sau 1.5 giây để hiển thị thông báo thành công
            setTimeout(() => {
                window.location.href = '/dashboard/index.html';
            }, 1500);
        }
    })
    .catch(error => {
        console.error('Đã xảy ra lỗi:', error);
        statusMsg.style.display = 'block';
        statusMsg.style.color = 'red';
        statusMsg.innerText = error.error || error.message || 'Đã xảy ra lỗi khi lưu thông tin.';
    });
});
