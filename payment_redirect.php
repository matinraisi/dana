<?php
// آپلود این فایل روی وردپرس در مسیر:
// public_html/dashboard/payment/callback/index.php
// این فایل callback از درگاه پرداخت رو به پنل منتقل می‌کنه

$params = $_SERVER['QUERY_STRING'];
$urlParams = [];
parse_str($params, $urlParams);

if (isset($urlParams['transid']) && isset($urlParams['status'])) {
    header("Location: https://panel.aihousesb.ir/dashboard/payment/callback/?" . $params);
    exit;
}

if (isset($urlParams['transid'])) {
    header("Location: https://panel.aqayepardakht.ir/startpay/" . $urlParams['transid']);
    exit;
}

header("Location: https://panel.aihousesb.ir/");
exit;
?>
