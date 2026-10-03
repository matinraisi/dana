document.addEventListener("DOMContentLoaded", function() {
    // پیدا کردن تمام فیلدهای تاریخ در ادمین
    const dateFields = document.querySelectorAll('input[type="date"], .vDateField');

    dateFields.forEach(field => {
        // فعال کردن تقویم شمسی روی فیلدها
        $(field).persianDatepicker({
            format: 'YYYY-MM-DD',
            autoClose: true,
            initialValue: false,
            calendar: {
                persian: {
                    locale: 'fa'
                }
            }
        });
    });
});