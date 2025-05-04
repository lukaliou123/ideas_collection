/**
 * 创业产品信息收集系统 - 主JavaScript文件
 */

// 在文档加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('创业产品信息收集系统前端已加载');
    
    // 初始化工具提示
    initTooltips();
    
    // 初始化过滤器
    initFilters();
});

/**
 * 初始化Bootstrap工具提示
 */
function initTooltips() {
    // 检查是否存在Bootstrap工具提示
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * 初始化产品过滤器
 */
function initFilters() {
    // 获取过滤器元素
    const filterForm = document.getElementById('filter-form');
    if (!filterForm) return;
    
    // 监听过滤表单提交
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        applyFilters();
    });
    
    // 获取重置按钮
    const resetBtn = document.getElementById('reset-filters');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            filterForm.reset();
            applyFilters();
        });
    }
}

/**
 * 应用过滤器并更新产品列表
 */
function applyFilters() {
    // 在实际应用中，可以使用AJAX请求获取过滤后的数据
    // 这里只是一个示例
    console.log('应用过滤器...');
    
    // 获取所有过滤参数
    const formData = new FormData(document.getElementById('filter-form'));
    const params = new URLSearchParams();
    
    for (const [key, value] of formData.entries()) {
        if (value) {
            params.append(key, value);
        }
    }
    
    // 更新URL并重新加载
    window.location.search = params.toString();
} 