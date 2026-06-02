// 1. Xử lý chọn đáp án (Đổi màu tím)
const options = document.querySelectorAll('.option');

options.forEach(opt => {
    opt.addEventListener('click', function() {
        // Xóa class selected của các ô khác
        options.forEach(o => o.classList.remove('selected'));
        // Thêm class selected vào ô vừa chọn
        this.classList.add('selected');
    });
});

// 2. Xử lý nút Xem kết quả
const btnResult = document.getElementById('btn-result');
const correctAns = document.getElementById('correct-answer');

btnResult.addEventListener('click', function() {
    // Hiện màu xanh cho câu C (Bà la môn giáo) bất kể người dùng chọn gì
    correctAns.classList.add('correct');
    
    // Disable click sau khi xem kết quả
    options.forEach(o => o.style.pointerEvents = 'none');
});