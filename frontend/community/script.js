const API_BASE_URL = '/api';
const POSTS_API_URL = `${API_BASE_URL}/posts`;
const ACTIVE_MEMBER_API_URL = `${API_BASE_URL}/active-member`;
const TOPICS_API_URL = `${API_BASE_URL}/topics-count`;
const CURRENT_USER_API_URL = `${API_BASE_URL}/current-user`;

let uploadedImagesBase64 = [];
// Đối tượng lưu trữ thông tin user hiện tại (Dùng làm bộ nhớ đệm Runtime)
let currentUser = { name: "Đang tải...", avatar: "https://i.pravatar.cc/150?img=47" };

// CACHING ĐỘC LẬP TOÀN BỘ PHẦN TỬ DOM
const DOM = {
    postsContainer: document.getElementById('postsContainer'),
    topicListContainer: document.getElementById('topicListContainer'),
    activeMemberContainer: document.getElementById('active-member-container'),
    postModal: document.getElementById('postModal'),
    openModalBtn: document.getElementById('openModalBtn'),
    closeModalBtn: document.getElementById('closeModalBtn'),
    cancelModalBtn: document.getElementById('cancelModalBtn'),
    submitPostBtn: document.getElementById('submitPostBtn'),
    postContentInput: document.getElementById('postContentInput'),
    topicSelect: document.getElementById('topicSelect'),
    dragZone: document.getElementById('dragZone'),
    fileInput: document.getElementById('fileInput'),
    previewSlotsContainer: document.getElementById('previewSlotsContainer'),
    modalUserAvatar: document.getElementById('modalUserAvatar'),
    modalUserName: document.getElementById('modalUserName')
};

// =========================================================================
// XỬ LÝ LẤY THÔNG TIN USER VỪA ĐĂNG NHẬP / ĐĂNG KÝ (TỐI ƯU CỰC MƯỢT)
// =========================================================================
async function initUserIdentity() {
    // Bước 1: Kiểm tra xem trang Đăng Nhập/Đăng Ký có lưu thông tin user vừa đăng nhập vào máy cục bộ không
    const savedUser = localStorage.getItem('loggedInUser');
    
    if (savedUser) {
        try {
            currentUser = JSON.parse(savedUser);
            renderUserToModal();
            return; // Đã có dữ liệu tức thì, không cần tốn tài nguyên gọi API nữa
        } catch (e) {
            console.error("Lỗi parse dữ liệu người dùng cục bộ", e);
        }
    }

    // Bước 2: Dự phòng nếu LocalStorage trống, gọi API Python để quét từ SQLite
    try {
        const response = await fetch(CURRENT_USER_API_URL);
        const result = await response.json();
        if (result.success) {
            currentUser = result.data;
            renderUserToModal();
            // Lưu lại vào bộ nhớ duyệt để lần sau load trang chạy mượt hơn
            localStorage.setItem('loggedInUser', JSON.stringify(currentUser));
        }
    } catch (error) {
        console.error("Không đồng bộ được thông tin định danh từ máy chủ:", error);
    }
}

// Hàm đẩy thông tin (Tên + Avatar) vào khối `<div class="post-author-tag">`
function renderUserToModal() {
    if (DOM.modalUserAvatar) DOM.modalUserAvatar.src = currentUser.avatar;
    if (DOM.modalUserName) DOM.modalUserName.textContent = currentUser.name;
}

// =========================================================================
// GỌI API & RENDER FEED BÀI VIẾT (TÍCH HỢP LAZY LOADING ẢNH)
// =========================================================================
async function fetchAndRenderPosts(tabName = 'Tổng quan') {
    if (!DOM.postsContainer) return;
    try {
        DOM.postsContainer.innerHTML = '<p style="text-align:center; padding: 20px; color: var(--text-muted); font-size: 14px;">Đang tải dữ liệu từ SQLite...</p>';
        
        const response = await fetch(`${POSTS_API_URL}?tab=${encodeURIComponent(tabName)}`);
        const result = await response.json();
        
        if (result.success) {
            const postsData = result.data;
            if (postsData.length === 0) {
                DOM.postsContainer.innerHTML = '<p style="text-align:center; padding: 40px; color: var(--text-muted);">Chưa có bài viết nào trg mục này hết m ơi! ✨</p>';
                return;
            }
            
            DOM.postsContainer.innerHTML = '';
            postsData.forEach(post => {
                let imagesGridHTML = '';
                if (post.images && post.images.length > 0) {
                    imagesGridHTML = `<div class="post-images-grid" data-count="${post.images.length}">`;
                    post.images.forEach(imgUrl => {
                        imagesGridHTML += `<img src="${imgUrl}" alt="Hình ảnh" class="post-img-item" loading="lazy">`;
                    });
                    imagesGridHTML += `</div>`;
                }
                
                const cardHTML = `
                    <article class="post-card">
                        <div class="post-user-info">
                            <div class="user-meta">
                                <img src="${post.authorAvatar}" alt="${post.authorName}" class="user-avatar" loading="lazy">
                                <div>
                                    <span class="user-name">${post.authorName}</span>
                                    <div class="post-time-tag">
                                        <span>${post.timeText}</span>
                                        <span class="post-tag-badge">${post.category}</span>
                                    </div>
                                </div>
                            </div>
                            <i class="fa-solid fa-ellipsis post-more-btn"></i>
                        </div>
                        <p class="post-text">${post.text}</p>
                        ${imagesGridHTML}
                        <div class="post-footer">
                            <div class="action-item"><i class="fa-solid fa-heart"></i> <span>${post.likes}</span></div>
                            <div class="action-item"><i class="fa-regular fa-comment"></i> <span>${post.comments} bình luận</span></div>
                            <div class="action-item"><i class="fa-regular fa-share-from-square"></i> <span>Chia sẻ</span></div>
                        </div>
                    </article>
                `;
                DOM.postsContainer.insertAdjacentHTML('beforeend', cardHTML);
            });
        }
    } catch (error) {
        console.error("Lỗi render bài viết:", error);
        DOM.postsContainer.innerHTML = '<p style="text-align:center; padding: 20px; color: red;">Lỗi kết nối máy chủ SQLite m ơi!</p>';
    }
}

// =========================================================================
// BẰNG XẾP HẠNG SIDEBAR VÀ THÀNH VIÊN TÍCH CỰC
// =========================================================================
async function fetchAndRenderSidebarTopics() {
    if (!DOM.topicListContainer) return;
    try {
        const response = await fetch(TOPICS_API_URL);
        const result = await response.json();
        if (result.success) {
            DOM.topicListContainer.innerHTML = '';
            result.data.forEach(topic => {
                if (topic.count > 0) {
                    DOM.topicListContainer.insertAdjacentHTML('beforeend', `
                        <div class="topic-item">
                            <span class="topic-name"># ${topic.name}</span>
                            <span class="topic-count">${topic.count} bài viết</span>
                        </div>
                    `);
                }
            });
        }
    } catch (error) {}
}

async function fetchAndRenderActiveMember() {
    if (!DOM.activeMemberContainer) return;
    try {
        const response = await fetch(ACTIVE_MEMBER_API_URL);
        const result = await response.json();
        if (result.success) {
            const member = result.data;
            DOM.activeMemberContainer.innerHTML = `
                <div class="active-member">
                    <img src="${member.avatar}" alt="Avatar" class="member-avatar" loading="lazy">
                    <div class="member-info">
                        <span class="member-name">${member.name}</span>
                        <span class="member-stats">${member.postCount} bài viết</span>
                    </div>
                </div>
            `;
        }
    } catch (error) {}
}

// =========================================================================
// ĐĂNG BÀI VIẾT MỚI: SỬ DỤNG THÔNG TIN NGƯỜI DÙNG VỪA ĐĂNG NHẬP ĐỘNG
// =========================================================================
if (DOM.submitPostBtn) {
    DOM.submitPostBtn.addEventListener('click', async () => {
        const textContent = DOM.postContentInput.value.trim();
        const selectedTopic = DOM.topicSelect.value;
        
        if (!textContent && uploadedImagesBase64.length === 0) {
            alert("Vui lòng điền nội dung hoặc chọn ảnh!");
            return;
        }
        
        // Tuyệt đối không viết cứng tên, bốc thẳng từ runtime identity của user vừa đăng nhập/đăng ký
        const newPostData = {
            authorName: currentUser.name,
            authorAvatar: currentUser.avatar,
            category: selectedTopic,
            text: textContent,
            images: uploadedImagesBase64
        };
        
        try {
            DOM.submitPostBtn.innerText = "Đang đăng...";
            DOM.submitPostBtn.disabled = true;
            
            const response = await fetch(POSTS_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newPostData)
            });
            const result = await response.json();
            
            if (result.success) {
                closeAndResetModal();
                const activeTab = document.querySelector('.tab-item.active');
                await fetchAndRenderPosts(activeTab ? activeTab.textContent.trim() : 'Tổng quan');
                await fetchAndRenderActiveMember();
                await fetchAndRenderSidebarTopics();
            }
        } catch (error) {
            console.error("Lỗi đăng bài viết:", error);
        } finally {
            DOM.submitPostBtn.innerText = "Đăng bài";
            DOM.submitPostBtn.disabled = false;
        }
    });
}

// UI LOGIC FOR FORM MODAL
if (DOM.openModalBtn) DOM.openModalBtn.addEventListener('click', () => DOM.postModal.classList.add('show'));

function closeAndResetModal() {
    if (!DOM.postModal) return;
    DOM.postModal.classList.remove('show');
    DOM.postContentInput.value = '';
    uploadedImagesBase64 = [];
    if (DOM.fileInput) DOM.fileInput.value = '';
    DOM.previewSlotsContainer.querySelectorAll('.slot').forEach(slot => slot.style.backgroundImage = 'none');
}

if (DOM.closeModalBtn) DOM.closeModalBtn.addEventListener('click', closeAndResetModal);
if (DOM.cancelModalBtn) DOM.cancelModalBtn.addEventListener('click', closeAndResetModal);
if (DOM.dragZone) DOM.dragZone.addEventListener('click', () => DOM.fileInput.click());

if (DOM.fileInput) {
    DOM.fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files).slice(0, 4 - uploadedImagesBase64.length);
        files.forEach((file) => {
            const reader = new FileReader();
            reader.onload = function(event) {
                uploadedImagesBase64.push(event.target.result);
                const slots = DOM.previewSlotsContainer.querySelectorAll('.slot');
                if (slots[uploadedImagesBase64.length - 1]) {
                    slots[uploadedImagesBase64.length - 1].style.backgroundImage = `url('${event.target.result}')`;
                }
            };
            reader.readAsDataURL(file);
        });
    });
}

document.querySelectorAll('.tab-item').forEach(tab => {
    tab.addEventListener('click', function() {
        const active = document.querySelector('.tab-item.active');
        if (active) active.classList.remove('active');
        this.classList.add('active');
        fetchAndRenderPosts(this.textContent.trim());
    });
});

// KHỞI ĐỘNG HỆ THỐNG
document.addEventListener("DOMContentLoaded", () => {
    initUserIdentity(); // Nhận diện tài khoản đăng ký/đăng nhập vừa thực hiện
    fetchAndRenderPosts('Tổng quan');
    fetchAndRenderActiveMember();
    fetchAndRenderSidebarTopics();
});
