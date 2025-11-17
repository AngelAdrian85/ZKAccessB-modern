// -*- coding: utf-8 -*-
___f=function(){
jQuery.validator.messages.required="必填"
jQuery.validator.messages.email="不是email位址"
jQuery.validator.messages.date="請輸入有效的日期：yyyy/mm/dd"
jQuery.validator.messages.dateISO="請輸入有效的 (ISO)日期：yyyy-mm-dd"
jQuery.validator.messages.wZBaseDateField="請輸入有效的日期：yyyy-mm-dd"
jQuery.validator.messages.wZBaseDateTimeField="請輸入有效的日期：yyyy-mm-dd hh:mm:ss"
jQuery.validator.messages.wZBaseTimeField="請輸入有效的時間：hh:mm:ss"
jQuery.validator.messages.wZBaseTime2Field="請輸入有效的時間：hh:mm"
jQuery.validator.messages.wZBaseIntegerField="請輸入整數"
jQuery.validator.messages.number="請輸入有效的數值."
jQuery.validator.messages.digits="只能輸入數字"
jQuery.validator.messages.equalTo="不一致"
jQuery.validator.messages.minlength=$.validator.format("最少{0}個字元")
jQuery.validator.messages.maxlength=$.validator.format("最多{0}個字元")
jQuery.validator.messages.rangelength=$.validator.format("必須是{0}到{1}個字元之間")
jQuery.validator.messages.range=$.validator.format("必須是{0}到{1}之間的值")
jQuery.validator.messages.max=$.validator.format("請輸入不大於 {0} 的值")
jQuery.validator.messages.min=$.validator.format("請輸入不小於 {0} 的值.")
jQuery.validator.messages.xPIN="只能輸入數字或字母。"
jQuery.validator.messages.xNum="只能輸入數字。"
jQuery.validator.messages.xMobile="手機號碼輸入不正確。"
jQuery.validator.messages.xTele="電話不正確。"
jQuery.validator.messages.xSQL="不能輸入\"或\'。"
}

___f();

if(typeof(catalog)=="undefined") {catalog={}}

//in file--D:\trunk\units\adms\mysite/templates\advenquiry.html
catalog["请选择一个字段"] = "請選擇一個欄位";
catalog["'满足任意一个' 值域必须是以','隔开的多个值"] = "'滿足任意一個' 資料欄必須是以','隔開的多個值";
catalog["输入的值错误"] = "輸入的值錯誤";
//in file--D:\trunk\units\adms\mysite/templates\base_page_frame.html
catalog["确定注销系统?"] = "確定登出系統?";
catalog["通讯失败"] = "通訊失敗";
catalog["确定"] = "確定";
catalog["取消"] = "取消";
catalog["服务器处理数据失败，请重试！错误码：-616"] = "伺服器處理資料失敗，請重試！錯誤碼：-616";
//in file--D:\trunk\units\adms\mysite/templates\data_edit.html
catalog["日志"] = "日誌";
//in file--D:\trunk\units\adms\mysite/templates\data_list.html
//in file--D:\trunk\units\adms\mysite/templates\DbBackupLog_list.html
catalog["请选择一条历史备份记录!"] = "請選擇一條歷史備份記錄!";
catalog["还原成功!"] = "復原成功!";
//in file--D:\trunk\units\adms\mysite/templates\DbBackupLog_opform_OpBackupDB.html
catalog["间隔时间不能超过一年"] = "間隔時間不能超過一年";
catalog["间隔时间不能小于24小时"] = "間隔時間不能小於24小時";
catalog["在当前时间的一个小时内只能备份一次"] = "在目前時間的一個小時內只能備份一次";
catalog["请先在服务控制台中设置数据库备份路径"] = "請先在服務控制台中設定資料庫備份路徑";
//in file--D:\trunk\units\adms\mysite/templates\DbBackupLog_opform_OpInitDB.html
catalog["全部"] = "全部";
//in file--D:\trunk\units\adms\mysite/templates\restore.html
catalog["数据格式必须是json格式!"] = "資料格式必須是json格式!";
//in file--D:\trunk\units\adms\mysite\iclock\templates\Area_opform_OpAdjustArea.html
catalog["请选择人员!"] = "請選擇人員!";
catalog["考勤"] = "考勤";
//in file--D:\trunk\units\adms\mysite\iclock\templates\Device_edit.html
catalog["设备名称不能为空"] = "設備名稱不能為空"
catalog["设备序列号不能为空"] = "設備序號不能為空";
catalog["通讯密码必须为数字"] = "連線密碼必須為數字";
catalog["请输入一个有效的IPv4地址"] = "請輸入有效的IPv4位址";
catalog["请输入一个有效的IP端口号"] = "請輸入有效的IP連接埠號";
catalog["请输入一个RS485地址"] = "請輸入RS485位址";
catalog["RS485地址必须为1到63之间的数字"] = "RS485位址必須為1到63之間的數字";
catalog["请选择串口号"] = "請選擇串口號";
catalog["请选择波特率"] = "請選擇波特率";
catalog["请选择设备所属区域"] = "請選擇設備所屬區域"
catalog["串口：COM"] = "串口：COM";
catalog[" 的RS485地址："] = " 的RS485位址：";
catalog[" 已被占用！"] = " 已被佔用！";
catalog[" 已添加过波特率不为："] = " 已新增過波特率不為：";
catalog[" 的设备！同一个串口下不允许存在多个波特率不同的设备。请重新选择波特率！"] = " 的設備！同一個串口下不允許存在多個波特率不同的設備。請重新選擇波特率！";
catalog["后台通讯忙，请稍后重试！"] = "後台通訊忙，請稍後重試！";
catalog["提示：设备连接成功，但获取设备扩展参数失败"] = "提示：設備連線成功，但取得設備延伸參數失敗";
catalog["，继续添加？"] = "，繼續新增？";
catalog["提示：设备连接成功，但控制器类型与实际不符，将修改为"] = "提示：設備連線成功，但控制器類型與實際不符，將修改為";
catalog["门控制器，继续添加？"] = "門控制器，繼續新增？";
catalog["一体机，继续添加？"] = "一體機，繼續新增？";
catalog["提示：设备连接成功，确定后将添加设备！"] = "提示：設備連線成功，確定後將新增設備！";
catalog["提示：设备连接失败（错误码："] = "提示：設備連線失敗（錯誤碼：";
catalog["），确定添加该设备？"] = "），確定新增該設備？";
catalog["提示：设备连接失败（原因："] = "提示：設備連線失敗（原因：";
catalog["您选择了[新增时删除设备中数据]，系统将自动删除设备中的数据(事件记录除外)，确定要继续？"] = "您選擇了[新增時刪除設備中資料]，系統將自動刪除設備中的資料(記錄除外)，確定要繼續？";
catalog["您没有选择[新增时删除设备中数据]，该功能仅用于系统功能演示和测试。请及时手动同步数据到设备，以确保系统中和设备中权限一致，确定要继续？"] = "您沒有選擇[新增時刪除設備中資料]，該功能僅用於系統功能演示和測試。請及時手動同步資料到設備，已確定系統中和設備中權限一致，確定要繼續？";
catalog["编辑设备信息("] = "編輯設備訊息(";
catalog["对不起，您没有访问该页面的权限，不能浏览更多信息！"] = "對不起，您沒有權限訪問該頁面，不能瀏覽更多訊息！";
//in file--D:\trunk\units\adms\mysite\iclock\templates\Dev_RTMonitor.html
catalog["确定要清除命令队列？"] = "確定要刪除指令佇列？";
catalog["清除缓存命令成功！请及时手动同步数据到设备，以确保系统中和设备中权限一致！"] = "刪除快取指令成功！請及時手動同步資料到設備，以確定系統中和設備中權限一致！";
catalog["清除缓存命令失败!"] = "刪除快取指令失敗!";
//in file--D:\trunk\units\adms\mysite\att\templates\att_USER_OF_RUN.html
catalog["员工排班表"] = "員工排班表";
catalog["临时排班表"] = "臨時排班表";
catalog["排班时间段详细明细"] = "排班時間段詳細資料";
catalog["排班时间段详细明细(仅显示三个月)"] = "排班時間段詳細資料(僅顯示三個月)";
catalog["排班时间段详细明细(仅显示到年底)"] = "排班時間段詳細資料(僅顯示到年底)";
//in file--D:\trunk\units\adms\mysite\att\templates\NUM_RUN_edit.html
catalog["请选择时段"] = "請選擇時段";
catalog["选择日期"] = "選擇日期";
catalog["第"] = "第";
catalog["天"] = "天";
catalog["周的周期不能大于52周"] = "周的週期不能大於52周";
catalog["月的周期不能大于12个月"] = "月的週期不能大於12個月";
catalog["第"]="第";
catalog["天"] = "天";
//in file--D:\trunk\units\adms\mysite\att\templates\NUM_RUN_list.html
catalog["时间段明细"] = "時間段詳細資料";
catalog["确定删除该时段吗？"] = "確定刪除該時段嗎？";
catalog["操作失败 {0} : {1}"] = "操作失敗 {0} : {1}";
//in file--D:\trunk\units\adms\mysite\att\templates\NUM_RUN_opform_OpAddTimeTable.html
catalog["已选择"] = "已選擇";
//in file--D:\trunk\units\adms\mysite\att\templates\USER_OF_RUN_opform_OpAddTempShifts.html
catalog["日期格式输入错误"] = "日期格式輸入錯誤";
catalog["日期格式不正确！"] = "日期格式不正確！"
catalog["夏令时名称不能为空！"] = "夏令時名稱不能為空！"
catalog["起始时间不能和结束时间相等！"] = "開始時間不能和結束時間相等！";
//in file--D:\trunk\units\adms\mysite\att\templates\USER_OF_RUN_opform_OpAddUserOfRun.html
catalog["请选择一个班次"] = "請選擇一個班次";
catalog["结束日期不能小于开始日期!"] = "結束日期不能小於開始日期!";
catalog["请输入开始日期和结束日期! "] = "請輸入開始日期和結束日期! ";
catalog["只能设置一个班次! "] = "只能設定一個班次! ";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccAntiBack_edit.html
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行反潜设置！"] = "目前選擇設備的延伸參數取得失敗，無法對該設備進行反潛設定！";
catalog["读取到错误的设备信息，请重试！"] = "讀取到錯誤的設備訊息，請重試！";
catalog["或"] = " 或 ";
catalog["反潜"] = " 反潛";
catalog["读头间反潜"] = "讀頭間反潛";
catalog["反潜"] = " 反潛";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccAntiBack_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccDoor_edit.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccFirstOpen_edit.html
catalog["当前门:"] = "目前的門:";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccFirstOpen_list.html
catalog["删除开门人员"] = "刪除開門人員";
catalog["请先选择要删除的人员！"] = "請先選擇要刪除的人員！";
catalog["确认要从首卡常开设置信息中删除开门人员？"] = "確認要從首卡常開設定訊息中刪除開門人員？";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccFirstOpen_opform_OpAddEmpToFCOpen.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccInterLock_edit.html
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行互锁设置！"] = "目前選擇設備的延伸參數取得失敗，無法對該設備進行互鎖設定！";
catalog["门:"] = "門: ";
catalog["与"] = "與";
catalog["互锁"] = " 互鎖";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccInterLock_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLevelSet_list.html
catalog["数据下载进度"] = "資料下載進度";
catalog["设备名称"] = "設備名稱";
catalog["总进度"] = "總進度";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLevelSet_opform_OpAddEmpToLevel.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLinkageIO_edit.html
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行联动设置！"] = "目前選擇設備的延伸參數取得失敗，無法對該設備進行連動設定！";
catalog["请输入联动设置名称！"] = "請輸入連動設定名稱！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLinkageIO_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMap_edit.html
catalog["请选择地图！"] = "請選擇地圖！";
catalog["图片格式无效！"] = "圖片格式無效！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardEmpGroup_list.html
catalog["浏览多卡开门人员组："] = "瀏覽多卡開門人員組：";
catalog[" 的人员"] = " 的人員";
catalog["当前不存在多卡开门人员组"] = "目前不存在多卡開門人員組";
catalog["删除人员"] = "刪除人員";
catalog["确认要从多卡开门人员组中删除人员？"] = "確認要從多卡開門人員組中刪除人員？";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardEmpGroup_opform_OpAddEmpToMCEGroup.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardSet_edit.html
catalog["请至少在一个组内填入开门人数！"] = "請至少在一個組內填入開門人數！";
catalog["至少两人同时开门！"] = "至少兩人同時開門！";
catalog["最多五人同时开门！"] = "最多五人同時開門！";
catalog["人"] = "人";
catalog["您还没有设置多卡开门人员组！请先添加！"] = "您還沒有設定多卡開門人員組！請先新增！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardSet_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccTimeSeg_edit.html
catalog["请在文本框内输入有效的时间！"] = "請在文字方塊內輸入有效的時間！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccWiegandFmt_list.html
catalog["对不起,您没有韦根卡格式设置的权限,不能进行当前操作！"] = "對不起,您沒有權限設定韋根卡格式,不能進行目前操作！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Door_Mng.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Door_Set.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Electro_Map.html
catalog["添加门到当前地图"] = "新增門到目前地圖";
catalog["请选择要添加的门！"] = "請選擇要新增的門！";
catalog["确定要删除当前电子地图："] = "確定要刪除目前電子地圖：";
catalog["添加辅助点到当前地图"] = "新增輔助點到目前地圖";
catalog["请选择要添加的辅助点！"] = "請選擇要新增的輔助點！";

//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_EmpLevel_Byemp.html
catalog["浏览人员："] = "瀏覽人員：";
catalog[" 所属权限组"] = " 所屬權限組";
catalog["当前不存在人员"] = "目前不存在人員";
catalog["删除所属权限组"] = "刪除所屬權限組";
catalog["请先选择要删除的权限组！"] = "請先選擇要刪除的權限組！";
catalog["确认要删除人员所属权限组？"] = "確認要刪除人員所屬權限組？";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_EmpLevel_Bylevel.html
catalog["数据处理进度"] = "資料處理進度";
catalog[" 的开门人员"] = " 的開門人員";
catalog["当前不存在权限组"] = "目前不存在權限組";
catalog["从权限组中删除"] = "從權限組中刪除";
catalog["权限组列表"]="權限組清單";
catalog["门列表"]="門清單"
catalog["人员列表"]="人員清單"
catalog["浏览 "]="瀏覽 "
catalog["可以进出的门"]=" 可以進出的門"
catalog["当前不存在人员"]="目前不存在人員"
catalog["以人员查询"]="以人員查詢"
catalog["以门查询"]="以門查詢 "
catalog["以权限组查询"]="以權限組查詢"
catalog["确认要从权限组中删除人员？"] = "確認要從權限組中刪除人員？";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Monitor_All.html
catalog["远程开门"] = "遠端開門";
catalog["选择开门方式"] = "選擇開門方式";
catalog["开门："] = "開門 ";
catalog[" 秒"] = " 秒";
catalog["常开"] = "常開";
catalog["启用当天常开时间段"] = "啟用當天常開時間段";
catalog["远程关门"] = "遠端關門";
catalog["选择关门方式"] = "選擇關門方式";
catalog["关门"] = "關門";
catalog["禁用当天常开时间段"] = "禁用當天常開時間段";
catalog["当前门处于常开状态，是否禁用当天常开时间段后关门？"] = "目前門處於常開狀態，是否禁用當天常開時間段後關門？";
catalog["当前已常开"] = "目前已常開";
catalog["发送请求失败！"] = "傳送請求失敗！";
catalog["发送请求成功！"] = "傳送請求成功！";
catalog["发送请求失败，请重试！"] = "傳送請求失敗，請重試！";
catalog["当前没有符合条件的门！"] = "目前沒有符合條件的門！";
catalog["请输入有效的开门时长！必须为1-254间的整数！"] = "請輸入有效的開門時長！必須為1-254間的整數！";
catalog["禁用"] = "禁用";
catalog["离线"] = "離線";
catalog["报警"] = "警報";
catalog["门开超时"] = "開門逾時";
catalog["关闭"] = "關閉";
catalog["打开"] = "開啟";
catalog["无门磁"] = "無門磁";
catalog["当前设备状态不支持该操作！"] = "目前設備狀態不支援該操作！";
catalog["该人员没有登记照片！"] = "該人員沒有登記照片！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform_alarm.html
catalog["导出报表"] = "匯出報表";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform_allevent.html
catalog["设置定时获取记录时间"] = "設定定時取得記錄時間";
catalog["每天"] = "每天 ";//特殊翻译请核对页面
catalog[" 点自动从设备获取新记录"] = " 點自動從設備取得新記錄";
catalog["注：请确保服务器在设置的时间点处于开机状态。"] = "註：請確定伺服器在設定的時間點處於開機狀態。";
catalog["定时下载记录时间设置成功！该设置将在软件服务或者操作系统重启后生效！"] = "定時下載記錄時間設定成功！該設定將在軟體服務或是操作系統重啟後生效！";
catalog["定时下载记录事件设置失败！请重试！"] = "定時下載記錄事件設定失敗！請重試！";
catalog["请输入有效的时间点(0-23)！"] = "請輸入有效的時間點(0-23)！";
catalog["无"] = "無";
catalog["注：1.请确保服务器在设置的时间点处于开机状态。<br/> 2.如需设置多个时间点，请以逗号分开。"] = "註：1.請確定伺服器在設定的時間點處於開機狀態。<br/> 2.如需設定多個時間點，請以逗號分開。";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform_emplevel.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Device_opform_OpChangeIPOfACPanel.html
catalog["请输入有效的IPv4地址！"] = "請輸入有效的IPv4位址！";
catalog["请输入有效的网关地址！"] = "請輸入有效的預設閘道！";
catalog["请输入有效的子网掩码！"] = "請輸入有效的子網路遮罩！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Device_opform_OpCloseAuxOut.html
catalog["获取设备扩展参数失败，当前操作不可用！"] = "取得設備延伸參數失敗，目前操作不可用！";
catalog["请选择要关闭的辅助输出点！"] = "請選擇要關閉的輔助輸出點！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Device_opform_OpSearchACPanel.html
catalog["退出"] = "離開";
catalog["正在搜索中,请等待!"] = "正在搜尋中,請等待!";
catalog["当前共搜索到的门禁控制器总数为："] = "目前共搜尋到的門禁控制器總數為：";
catalog["自定义设备名称"] = "自訂設備名稱";
catalog["新增时删除设备中数据"] = "新增時刪除設備中資料";
catalog["设备名称不能为空，请重新添加设备！"] = "設備名稱不能為空，請重新新增設備！";
catalog["的设备添加成功！"] = " 的設備新增成功！";
catalog["已添加设备数："] = "已新增設備數：";
catalog["IP地址："] = "IP位址：";
catalog[" 已存在！"] = "已存在！";
catalog["序列号："] = "序號：";
catalog["IP地址为："] = "IP位址為：";
catalog[" 的设备添加失败！原因："] = " 的設備新增失敗！原因：";
catalog[" 的设备添加异常！原因："] = " 的設備新增異常！原因：";
catalog["的设备添加成功，但设备扩展参数获取失败！原因："] = " 的設備新增成功，但設備延伸參數取得失敗！原因：";
catalog["设备连接成功，但无数据返回，添加设备失败！"] = "設備連線成功，但無資料返回，新增設備失敗！";
catalog["设备连接失败(错误码："] = "設備連線失敗(錯誤碼： ";
catalog[")，无法添加该设备！"] = ")，無法新增該設備！";
catalog["设备连接失败(原因："] = "設備連線失敗(原因：";
catalog["修改设备IP地址"] = "修改設備IP位址";
catalog["原IP地址"] = "原IP位址";
catalog["新IP地址"] = "新IP位址";
catalog["网关地址"] = "預設閘道";
catalog["子网掩码"] = "子網路遮罩";
catalog["请输入设备通讯密码:"] = "請輸入設備連線密碼:";
catalog["新的IP地址不能为空！"] = "新的IP位址不能為空！";
catalog["请输入一个有效的IPv4地址！"] = "請輸入有效的IPv4位址！";
catalog["请输入一个有效的网关地址！"] = "請輸入有效的預設閘道！";
catalog["请输入一个有效的子网掩码！"] = "請輸入有效的子網路遮罩！";
catalog["该IP地址的设备已存在或该IP地址已被使用，不能添加！请重新输入！"] = "該IP位址的設備已存在或該IP位址已被使用，不能新增！請重新輸入！";
catalog["操作失败！原因："] = "操作失敗！原因：";
catalog["设备连接成功，但修改IP地址失败！"] = "設備連線成功，修改IP位址失敗！";
catalog["设备连接失败，故修改IP地址失败！"] = "設備連線失敗，修改IP位址失敗！";
catalog["没有搜索到门禁控制器！"] = "沒有搜尋到門禁控制器！";
//in file--D:\trunk\units\adms\mysite\personnel\templates\Department_list.html
catalog["显示部门树"] = "顯示部門樹";
catalog["隐藏部门树"] = "隱藏部門樹";
//in file--D:\trunk\units\adms\mysite\personnel\templates\EmpChange_edit.html
catalog["请选择一个调动栏位"] = "請選擇一個調動欄位";
//in file--D:\trunk\units\adms\mysite\personnel\templates\EmpItemDefine_list.html
catalog["部门花名册"] = "部門名冊";
catalog["学历构成分析表"] = "學歷構成分析表";
catalog["人员流动表"] = "人員流動表";
catalog["人员卡片清单"] = "人員卡片清單";
catalog["请选择开始日期和结束日期"] = "請選擇開始日期和結束日期";
catalog["开始日期不能大于结束日期"] = "開始日期不能大於結束日期";
//in file--D:\trunk\units\adms\mysite\personnel\templates\Employee_edit.html
catalog["图片格式无效!"] = "圖片格式無效";
catalog["人员编号必须为数字"] = "人員編號必須為數字";
catalog["请输入有效的E_mail!"]="請輸入有效的E_mail!";
catalog["身份证号码不正确"] = "身份證號碼不正確";
catalog["没有可选的门禁权限组！"] = "沒有可選的門禁權限組！";
catalog["指纹模板错误，请立即联系开发人员！"] = "指紋範本錯誤，請立即聯絡開發人員！";
catalog["指纹模板错误，请重新登记！"] = "指紋範本錯誤，請重新登記！";

catalog["修改密码"] = "修改密碼";
catalog["旧密码："] = "舊密碼：";
catalog["新密码："] = "新密碼：";
catalog["确认密码："] = "確認密碼：";
catalog["最大6位整数"] ="最大6位整數";

//in file--D:\trunk\units\adms\mysite\personnel\templates\Employee_list.html
//in file--D:\trunk\units\adms\mysite\personnel\templates\Employee_opform_OpAddLevelToEmp.html
//in file--D:\trunk\units\adms\mysite\personnel\templates\IssueCard_opform_OpBatchIssueCard.html
catalog["每次发卡数量不能超过100"] = "每次發卡數量不能超過100";
catalog["起始编号长度不能超过"] = "起始編號長度不能超過";
catalog["位"] = " 位";
catalog["结束编号长度不能超过"] = "結束編號長度不能超過";
catalog["起始人员编号与结束人员编号的长度位数不同！"] = "起始人員編號與結束人員編號的長度位數不同！";
//in file--D:\trunk\units\adms\mysite\personnel\templates\LeaveLog_list.html
//in file--D:\trunk\units\adms\mysite\worktable\templates\worktable_common_monitor.html
catalog["点击查看消息详情"] = "點擊檢視訊息詳情";
catalog["删除该消息"] = "刪除該訊息";
catalog["公告详情"] = "公告詳情";
//in file--D:\trunk\units\adms\mysite\worktable\templates\worktable_common_opt.html
catalog["保存成功!"] = "儲存成功";
catalog["人员选择:"] = "選擇人員:";
//in file--D:\trunk\units\adms\mysite\worktable\templates\worktable_common_search.html
catalog["人员查询"] = "人員查詢";
catalog["人员编号"] = "人員編號";
catalog["姓名"] = "姓名";
catalog["身份证号查询"] = "身份證號碼查詢";
catalog["身份证号码"] = "身份證號碼";
catalog["考勤设备查询"] = "考勤設備查詢";
catalog["离职人员查询"] = "離職人員查詢";
catalog["考勤原始数据查询"] = "考勤原始資料查詢";
catalog["员工调动查询"] = "員工調動查詢";
catalog["卡片查询"] = "卡片查詢";
catalog["卡号"] = "卡號";
catalog["部门查询"] = "部門查詢";
catalog["部门编号"] = "部門編號";
catalog["部门名称"] = "部門名稱";
catalog["补签卡查询"] = "補簽記錄查詢";
catalog["服务器加载数据失败,请重试!"] = "伺服器載入資料失敗,請重試!";
//in file--D:\trunk\units\adms\mysite\media\jslib\calculate.js
catalog["补签卡"] = "補簽記錄";
catalog["补请假"] = "補請假";
catalog["新增排班"] = "新增排班";
catalog["临时排班"] = "臨時排班";
catalog["结束日期不能大于今天"] = "結束日期不能大於今天";
catalog["统计只能当月日期，或者天数不能超过开始日期的月份天数！ "] = "統計只能當月日期，或是天數不能超過開始日期的月份天數！";
catalog["统统计的时间可能会较长，请耐心等待"] = "統統計的時間可能會較長，請耐心等待";
catalog["请选择人员或部门"] = "請選擇人員或部門";
catalog["统计结果详情"] = "統計結果";
catalog["每日考勤统计表"] = "每日考勤統計表";
catalog["考勤明细表"] = "考勤明細表";
catalog["请假明细表"] = "請假明細表";
catalog["考勤统计汇总表"] = "考勤統計總表";
catalog["原始记录表"] = "原始記錄表";
catalog["补签卡表"] = "補簽記錄表";
catalog["请假汇总表"] = "請假總表";
catalog["请选择开始日期或结束日期!"] = "請選擇開始日期或結束日期!";
catalog["开始日期不能大于结束日期!"] = "開始日期不能大於結束日期!";
catalog["最多只能查询31天的数据!"] = "最多只能查詢31天的資料!";
catalog["请在查询结果中选择人员！"] = "請在查詢結果中選擇人員！";
catalog["取消"] = "取消";
//in file--D:\trunk\units\adms\mysite\media\jslib\CDrag.js
catalog["展开"] = "展開";
catalog["收缩"] = "收起";
catalog["自定义工作面板"] = "自訂工作面板";
catalog["锁定"] = "鎖定";
catalog["解除"] = "解除";
catalog["常用操作"] = "常用操作";
catalog["常用查询"] = "常用查詢";
catalog["考勤快速上手"] = "考勤快速上手";
catalog["门禁快速上手"] = "門禁快速上手";
catalog["系统提醒、公告"] = "系統提醒、公告";
catalog["人力构成分析"] = "人力構成分析";
catalog["最近门禁异常事件"] = "最近門禁異常事件";
catalog["本日出勤率"] = "本日出勤率";
catalog["加载中......"] = "載入中......";
//in file--D:\trunk\units\adms\mysite\media\jslib\datalist.js
catalog["是否"] = "是否";
catalog["选择所有 {0}(s)"] = "選擇所有 {0}";
catalog["选择 {0}(s): "] = "選擇 {0}:";
catalog["服务器处理数据失败，请重试！"] = "伺服器處理資料失敗，請重試！";
catalog["新建相关数据"] = "新增關聯資料";
catalog["浏览相关数据"] = "瀏覽關聯資料";
catalog["添加"] = "新增";
catalog["浏览"] = "瀏覽";
catalog["编辑"] = "編輯";
catalog["编辑这行数据"] = "編輯資料";
catalog["升序"] = "升序";
catalog["降序"] = "降序";
//in file--D:\trunk\units\adms\mysite\media\jslib\datalistadd.js
catalog["该模型不支持高级查询功能"] = "該模型不支援進階查詢功能";
catalog["高级查询"] = "進階查詢";
catalog["导入"] = "匯入";
catalog["请选择一个上传的文件!"] = "請選擇一個上傳的檔案!";
catalog["标题行号必须是数字!"] = "標題行號必須是數字!";
catalog["记录行号必须是数字!"] = "記錄行號必須是數字!";
catalog["请选择xls文件!"] = "請選擇xls檔案!";
catalog["请选择csv文件或者txt文件!"] = "請選擇csv檔案或是txt檔案!";
catalog["文件标头"] = "檔案標頭";
catalog["文件记录"] = "檔案記錄";
catalog["表字段"] = "表欄位";
catalog["请先上传文件！"] = "請先上傳檔案！";
catalog["导出"] = "匯出";
catalog["页记录数只能为数字"] = "頁記錄數只能為數字";
catalog["页码只能为数字"] = "頁碼只能為數字";
catalog["记录数只能为数字"] = "記錄數只能為數字";
catalog["用户名"] = "使用者名";
catalog["动作标志"] = "動作標誌";
catalog["增加"] = "增加";
catalog["修改"] = "修改";
catalog["删除"] = "删除";
catalog["其他"] = "其他";
//in file--D:\trunk\units\adms\mysite\media\jslib\electro_map.js
catalog["地图宽度到达上限(1120px)，不能再放大！"] = "地圖寬度到達上限(1120px)，不能再拉近！";
catalog["地图宽度到达下限(400px)，不能再缩小！"] = "地圖寬度到達下限(400px)，不能再拉遠！";
catalog["地图高度到达下限(100px)，不能再缩小！"] = "地图高度到达下限(100px)，不能再缩小！";
catalog["门图标的位置（Top或Left）到达下限，请稍作调整后再进行缩小操作！"] = "門圖示的位置（Top或Left）到達下限，請稍作調整後再進行拉遠操作！";

//in file--D:\trunk\units\adms\mysite\media\jslib\importAndExport.js
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.plus.js
catalog["信息提示"] = "訊息提示";
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.plus.js
catalog["日期"] = "日期";
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.zcommon.js
catalog["标签页不能多于6个!"] = "標籤頁不能多於6個!";
catalog["按部门查找"] = "按部門搜尋";
catalog["选择部门下所有人员"] = "選擇部門下所有人員";
catalog["(该部门下面的人员已经全部选择!)"] = "(該部門下面的人員已經全部選擇!)";
catalog["按人员编号/姓名查找"] = "按人員編號/姓名搜尋";
catalog["按照人员编号或姓名查找"] = "按照人員編號或姓名搜尋";
catalog["查询"] = "查詢";
catalog["请选择部门"] = "請選擇部門";
catalog["该部门下面的人员已经全部选择!"] = "該部門下面的人員已經全部選擇!";
catalog["打开选人框"] = "開啟選人框";
catalog["收起"] = "收起";
catalog["已选择人员"] = "已選擇人員";
catalog["清除"] = "刪除";
catalog["编辑还未完成，已临时保存，是否取消临时保存?"] = "編輯還未完成，已臨時儲存，是否取消臨時儲存?";
catalog["恢复"] = "恢復";
catalog["会话已经过期或者权限不够,请重新登入!"] = "連線已經過期或是權限不夠,請重新登入!";
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.zgrid.js
catalog["没有选择要操作的对象"] = "沒有選擇要操作的對象";
catalog["进行该操作只能选择一个对象"] = "進行該操作只能選擇一個對像";
catalog["相关操作"] = "相關操作";
catalog["共"] = "共";
catalog["记录"] = "記錄";
catalog["页"] = "頁";
catalog["首页"] = "第一頁";
catalog["前一页"] = "前一頁";
catalog["后一页"] = "後一頁";
catalog["最后一页"] = "最後一頁";
catalog["选择全部"] = "選擇全部";
//in file--D:\trunk\units\adms\mysite\media\jslib\widgets.js
catalog["January February March April May June July August September October November December"] = "一月 二月 三月 四月 五月 六月 七月 八月 九月 十月 十一月 十二月";
catalog["S M T W T F S"] = "日 一 二 三 四 五 六";
//---------------------------------------------------------
catalog["记录条数不能超过10000"] = "記錄數不能超過10000";
catalog["请输入大于0的数字"] = "請輸入大於0的數字";
catalog["当天存在员工排班时"] = "當天存在員工排班時";

catalog["暂无提醒及公告信息"] = "暫無提醒及公告訊息";
catalog["关于"] = "關於 ";
catalog["版本号"] = "版本號";
catalog["产品ID"] = "產品ID";
catalog["本系统建议使用浏览器"] = "本系統建議使用瀏覽器";
catalog["显示器分辨率"] = "顯示器解析度";
catalog["及以上像素"] = "及以上像素";
catalog["软件运行环境"] = "軟體運行環境";
catalog["系统默认"] = "系統預設";

catalog["photo"] = "照片";
catalog["table"] = "清單";

catalog["此卡已添加！"] = "此卡已新增！";
catalog["卡号不正确！"] = "卡號不正確！";
catalog["请输入要添加的卡号！"] = "請輸入要新增的卡號！";
catalog["请选择刷卡位置！"] = "請選擇刷卡位置！";
catalog["请选择人员！"] = "請選擇人員！";
catalog["table"] = "清單";
catalog["table"] = "清單";
catalog["首字符不能为空!"]="首字元不能為空!";
catalog["密码长度必须大于4位!"]="密碼長度必須大於4位!";

catalog["当前列表中没有卡可供分配！"] = "目前清單中沒有卡可供分配！";
catalog["当前列表中没有人员需要分配！"] = "目前清單中沒有人員需要分配！";
catalog["没有已分配人员！"] = "沒有已分配人員！";
catalog["请先点击停止读取！"] = "請先點擊停止讀取！";
catalog["请选择需要分配的人员！"] = "請選擇需要分配的人員！";

catalog["请选择一个介于1到223之间的数值！"] = "請選擇一個介於1到223之間的數值！";
catalog["备份路径不存在，是否自动创建？"] = "備份路徑不存在，是否自動建立？";
catalog["处理中"] = "處理中"
catalog["是"] = "是"
catalog["否"] = "否"
//------------------------------------------------------------------------
//in file--D:\trunk\units\adms\mysite\media\jslib\worktable.js
catalog["已登记指纹"] = "已登記指紋:"
//人员判断哪里 验证 输入不合法
catalog["不合法"] = "不合法";

catalog["通讯密码"] = "連線密碼";

catalog["登记指纹功能只支持IE浏览器"] = "登記指紋功能只支援IE瀏覽器";

catalog["请安装指纹仪驱动"] = "請安裝指紋儀驅動";

catalog["解析xml文件出错"] = "解析xml檔案出錯";

catalog["该通道已达最大访问量！"] = "該頻道已達最大訪問量！";

catalog["当前没有可用的角色,请先添加角色"] = "目前沒有可用的角色,請先新增角色";

catalog["当前设备IP地址和服务器不在同一网段，请先将其调整到一个网段，再尝试添加！"] = "目前設備IP位址和伺服器不在同一網段，請先將其調整到一個網段，再嘗試新增！";

catalog["数据库将备份到:"]="資料庫將備份到:";

//
catalog["所选的部门总数不能大于2000"]="所選的部門總數不能大於2000";

catalog["操作成功！"] = "操作成功！";
catalog["操作失败！"] = "操作失敗！";
catalog["服务器处理数据失败，请重试！错误码："] = "伺服器處理資料失敗，請重試！錯誤碼：";
catalog["重连间隔时间必须为整数！"] = "重連間隔時間必須為整數！";
catalog["设置成功，重启服务后生效！"]="設定成功，重啟服務後生效！";
catalog["设置成功！"]="設定成功！";

//catalog["保存参数成功！"] = "參數儲存成功！";
catalog["获取记录时间点不能为空！"] = "取得記錄時間點不能為空！";

catalog["用户注册失败，请检查设备配置"] = "使用者註冊失敗，請檢查設備配置";
catalog["目前该功能仅支持IE系列及IE内核的浏览器，请更换！"] = "目前該功能僅支援IE系列及IE內核的瀏覽器，請更換！";
catalog["请选择视频设备！"] = "請選擇視訊設備！";
catalog["控件初始化失败，请确定视频设备类型是否选择正确或重装控件！"] = "元件初始化失敗，請確定視訊設備類型是否選擇正確或重裝元件！";
catalog["预览失败"] = "預覽失敗";

catalog["邮箱地址格式不正确"] = "信箱位址格式不正確";
catalog["请输入邮箱地址"] = "請輸入信箱位址";
catalog["邮件通知"] = "信件通知";
catalog["报警监控"] = "警報監控";
catalog["辅助输入"] = "輔助輸入";
catalog["辅助输出"] = "輔助輸出";
catalog["邮件通知"] = "信件通知";
catalog["请输入邮箱地址"] = "請輸入信箱位址";
catalog["请输入邮箱地址，多个地址用 ';' 隔开"] = "請輸入信箱位址，多個位址用 ';' 隔開";
catalog["邮件发送成功!"] = "信件傳輸成功!";
catalog["邮件发送失败!"] = "信件傳送失敗!";
catalog["邮件发送失败,门禁参数配置中邮箱配置错误!"] = "信件傳送失敗,門禁參數配置中信箱配置錯誤!";
catalog["请选择报警设备!"] = "請選擇警報設備!";

catalog["门状态"] = "門狀態";
catalog["门锁状态"] = "門鎖狀態";
catalog["报警类型"] = "警報類型";
catalog["门关报警"] = "關門警報";
catalog["门开报警"] = "開門警報";
catalog["门开超时"] = "開門逾時";
catalog["解锁"] = "解鎖";
catalog["锁定"] = "鎖定";
catalog["没有报警"] = "沒有警報";
catalog["防拆"] = "防拆";
catalog["胁迫密码开门"] = "脅迫密碼開門";
catalog["门被意外打开"] = "門被意外開啟";
catalog["请先关闭门！"] = "請先關閉門！";
catalog["胁迫开门"] = "脅迫開門";
catalog["胁迫指纹开门"] = "脅迫指紋開門";

//in file--D:\trunk\units\adms\mysite\ Acc_Reportform.html
catalog["视频服务器登录失败，请确认后重试！原因："] = "視訊伺服器登入失敗，請確認後重試！原因：";
catalog["视频服务器登录失败，请确认后重试！错误码："] = "視訊伺服器登入失敗，請確認後重試！錯誤碼：";
catalog["视频回放失败，请确认后重试！原因："] = "視訊重播失敗，請確認後重試！原因：";
catalog["视频回放失败，请确认后重试！错误码："] = "視訊重播失敗，請確認後重試！錯誤碼：";
catalog["视频服务器登录失败，请确认后重试！"] = "視訊伺服器登入失敗，請確認後重試！"
//视频模块国际化-start
catalog["当前系统中没有添加视频服务器，请添加！"] = "目前系統中沒有新增視訊伺服器，請新增！";
catalog["视频通道不能重复选择，请重新选择！"] = "視訊頻道不能重複選擇，請重新選擇！";
catalog["读头"] = "讀頭";
catalog["名称"] = "名稱";
catalog["视频时长不能小于0，请输入正确的视频时长!"] = "視訊時長不能小於0，請輸入正確的視訊時長!";
catalog["录像时长不能小于0，请输入正确的录像时长!"] = "錄影時長不能小於0，請輸入正確的錄影時長!";
catalog["添加摄像机到当前地图"] = "新增攝影機到目前地圖";
catalog["请选择要添加的摄像头！"] = "請選擇要新增的攝影機！";
catalog["视频查询"] = "視訊查詢";
catalog["视频联动"] = "視訊連動";
catalog["视频加载中，请稍侯......"] = "視訊載入中，請稍侯......";
catalog["该通道已达最大访问量或视频服务器未连接!"] = "該頻道已達最大訪問量或視訊伺服器未連線!";
catalog["预览失败，请确认后重试！原因："] = "預覽失敗，請確認後重試！原因：";
catalog["预览失败，请确认后重试！错误码："] = "預覽失敗，請確認後重試！錯誤碼：";
catalog["无此权限！"] = "無此權限！";
catalog["没有录像文件！"] = "沒有錄影檔案！";
catalog["该通道已达最大访问量或视频服务器未连接！"] = "該頻道已達最大訪問量或視訊伺服器未連線！";
catalog["从视频服务器导出失败！"] = "從視訊伺服器匯出失敗！";
catalog["从视频服务器导出成功！"] = "從視訊伺服器匯出成功！";
catalog["视频弹出窗口高度必须为整数！"] = "視訊跳出視窗高度必須為整數！";
catalog["请选择需要设置的对象!"] = "請選擇需要設定的對象!";
catalog["请启用当前视频设备下被禁用的视频通道！"] = "請啟用目前視訊設備下被禁用的視訊頻道！";
//海康dvr last_error
catalog["HIKVISION_ERROR_1"] = "使用者名密碼錯誤";
catalog["HIKVISION_ERROR_4"] = "頻道號錯誤";
catalog["HIKVISION_ERROR_5"] = "連線到DVR的用戶端個數超過最大";
catalog["HIKVISION_ERROR_7"] = "連線伺服器失敗";
catalog["HIKVISION_ERROR_8"] = "向伺服器傳送失敗";
catalog["HIKVISION_ERROR_10"] = "從DVR取得資料時逾時";
catalog["HIKVISION_ERROR_17"] = "參數錯誤";
catalog["HIKVISION_ERROR_19"] = "沒有硬碟";
catalog["HIKVISION_ERROR_20"] = "硬碟號錯誤";
catalog["HIKVISION_ERROR_21"] = "伺服器硬碟滿";
catalog["HIKVISION_ERROR_22"] = "伺服器硬碟出錯";
catalog["HIKVISION_ERROR_24"] = "伺服器忙碌";
catalog["HIKVISION_ERROR_28"] = "DVR資源不足";
catalog["HIKVISION_ERROR_29"] = "DVR操作失敗";
catalog["HIKVISION_ERROR_33"] = "重播時伺服器沒有特殊的檔案，34";
catalog["HIKVISION_ERROR_36"] = "上次的操作還沒有完成";
catalog["HIKVISION_ERROR_38"] = "播放出錯";
catalog["HIKVISION_ERROR_46"] = "個數達到最大";
catalog["HIKVISION_ERROR_47"] = "使用者不存在";
catalog["HIKVISION_ERROR_52"] = "使用者數達到最大";
catalog["HIKVISION_ERROR_74"] = "取消時使用者ID正在進行某操作";
catalog["HIKVISION_ERROR_90"] = "設備正在備份";

catalog["许可信息"] = "授權訊息";

catalog["请切换为英文输入法状态！"] = "請切換為英文輸入法狀態！";

catalog["许可信息"] = "授權訊息";
catalog["请选择每个扩展板的继电器数量！"] = "請選擇每個延伸板的繼電器數量！";

//登录页面验证
catalog["比对验证中，请稍等!"] = "比對驗證中，請稍等!";
catalog["验证失败，请重试!"] = "驗證失敗，請重試!";
catalog["10.0指纹算法许可失败!"] = "10.0指紋算法許可失敗!";
catalog["验证通过，登录系统!"] = "驗證通過，登入系統!";
catalog["获取指纹失败，请重试!"] = "取得指紋失敗，請重試!";
catalog["登记指纹功能只支持IE浏览器"] = "登記指紋功能只支援IE瀏覽器";
catalog["请安装指纹仪驱动"] = "請安裝指紋儀驅動";

//访客
catalog["进入地点"] = "進入地點";
catalog["离开地点"] = "離開地點";
catalog["被访人姓名"] = "被訪人姓名";
catalog["被访人姓氏"] = "被訪人姓氏";
catalog["是否重新打印访客单？"] = "是否重新列印訪客單？";
catalog["没有注册读写器控件，是否下载控件？"] = "沒有註冊讀寫器元件，是否下載元件？";
catalog["没有注册扫描仪控件，是否下载控件？"] = "沒有註冊掃瞄器元件，是否下載元件？";
catalog["暂时不支持该证件类型！"] = "暫時不支援該證件類型！";
catalog["请选择正确的证件类型或调整证件的位置！"] = "請選擇正確的證件類型或調整證件的位置！";
catalog["加载核心失败！"] = "載入核心失敗！";
catalog["初始化失败！"] = "初始化失敗！";
catalog["请放好身份证！"] = "請放好身份證！";
catalog["没有检测到身份证阅读器！"] = "沒有偵測到身份證讀取器！";
catalog["目前该功能仅支持二代身份证！"] = "目前該功能僅支援二代身份證！";
catalog["没有可选的权限组！"] = "沒有可選的權限組！";
catalog["卡号已存在，如果确认将重新发卡，请先清除该卡原持卡人"] = "卡號已存在，若果確認將重新發卡，請先刪除該卡原持卡人";

//init_base_frame.js
catalog["正式版许可"] = "正式版授權";
catalog["试用版许可"] = "試用版授權";

