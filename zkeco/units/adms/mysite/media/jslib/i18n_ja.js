// -*- coding: utf-8 -*-
___f=function(){
jQuery.validator.messages.required="必須"
jQuery.validator.messages.email="E-mailアドレス無"
jQuery.validator.messages.date="有効な日付形式: yyyy/mm/dd.で入力してください"
jQuery.validator.messages.dateISO="有効な日付形式: yyyy-mm-ddで入力してください."
jQuery.validator.messages.wZBaseDateField="有効な日付形式: yyyy-mm-ddで入力してください"
jQuery.validator.messages.wZBaseDateTimeField="有効な日付: yyyy-mm-dd hh:mm:ssを入力してください."
jQuery.validator.messages.wZBaseTimeField="有効な時間を: hh:mm:ss.入力してください"
jQuery.validator.messages.wZBaseIntegerField="整数を入力してください"
jQuery.validator.messages.number="有効な値を入力してください"
jQuery.validator.messages.digits="数値のみ許可されます"
jQuery.validator.messages.equalTo="異なります"
jQuery.validator.messages.minlength=$.validator.format("at least {0} character(s)")
jQuery.validator.messages.maxlength=$.validator.format("at most {0} character(s)")
jQuery.validator.messages.rangelength=$.validator.format("between {0} and {1} characters")
jQuery.validator.messages.range=$.validator.format("between {0} and {1}")
jQuery.validator.messages.max=$.validator.format("Please input a value not larger than {0}.")
jQuery.validator.messages.min=$.validator.format("Please input a value not smaller than {0}.")
jQuery.validator.messages.xPIN="数値または文字のみ許可されます"
jQuery.validator.messages.xNum="数値のみ許可されます"
jQuery.validator.messages.xMobile="不正携帯電話番号"
jQuery.validator.messages.xTele="不正電話番号"
jQuery.validator.messages.xSQL="\" or \' not allowed."
}

___f();

if(typeof(catalog)=="undefined") {catalog={}}

//in file--D:\trunk\units\adms\mysite/templates\advenquiry.html
catalog["请选择一个字段"] = "項目を選択して下さい";
catalog["'满足任意一个' 值域必须是以','隔开的多个值"] = "複合値のみ分割されました','値範囲";
catalog["输入的值错误"] = "不正入力値";
//in file--D:\trunk\units\adms\mysite/templates\base_page_frame.html
catalog["确定注销系统?"] = "ログアウトしますか?";
catalog["通讯失败"] = "失敗";
catalog["确定"] = "OK";
catalog["确认"] = "OK";
//in file--D:\trunk\units\adms\mysite/templates\data_edit.html
catalog["日志"] = "履歴";
//in file--D:\trunk\units\adms\mysite/templates\data_list.html
//in file--D:\trunk\units\adms\mysite/templates\DbBackupLog_list.html
catalog["请选择一条历史备份记录!"] = "入場履歴バックアップを選択して下さい!";
catalog["还原成功!"] = "リストア成功!";
//in file--D:\trunk\units\adms\mysite/templates\DbBackupLog_opform_OpBackupDB.html
catalog["间隔时间不能超过一年"] = "年をまたぐ間隔はできません";
catalog["间隔时间不能小于24小时"] = "間隔は24時間以内です";
catalog["在当前时间的一个小时内只能备份一次"] = "現在時間の一時間以内に一度だけバックアップされます!";
catalog["请先在服务控制台中设置数据库备份路径"] = "データベースバックアップパスを最初に設定してください";
//in file--D:\trunk\units\adms\mysite/templates\DbBackupLog_opform_OpInitDB.html
catalog["全部"] = "全て";
//in file--D:\trunk\units\adms\mysite/templates\restore.html
catalog["数据格式必须是json格式!"] = "データフォーマットはjson方式です!";
//in file--D:\trunk\units\adms\mysite\iclock\templates\Area_opform_OpAdjustArea.html
catalog["请选择人员!"] = "ユーザーを選択して下さい!";
catalog["考勤"] = "勤怠";
//in file--D:\trunk\units\adms\mysite\iclock\templates\Device_edit.html
catalog["设备名称不能为空"] = "機器名は空白にできません";
catalog["设备序列号不能为空"] = "機器シリアルナンバーは空白にできません";
catalog["通讯密码必须为数字"] = "通信パスワードは数字です";
catalog["请输入一个有效的IPv4地址"] = "IPv4アドレスを入力してください";
catalog["请输入一个有效的IP端口号"] = "IPポート番号を入力してください";
catalog["请输入一个RS485地址"] = "RS485アドレスを入力してください";
catalog["RS485地址必须为1到63之间的数字"] = "RS485アドレスは、1～63の数字です";
catalog["请选择串口号"] = "シリアルポートNoを選択して下さい";
catalog["请选择波特率"] = "ボーレートを選択して下さい";
catalog["请选择设备所属区域"] = "機器のエリアを選択して下さい";
catalog["串口：COM"] = "Serial port COM";
catalog[" 的RS485地址："] = "'s RS485アドレス";
catalog[" 已被占用！"] = " 占有されました！";
catalog[" 已添加过波特率不为："] = " ボーレートが設定されていない機器が追加されました：";
catalog[" 的设备！同一个串口下不允许存在多个波特率不同的设备。请重新选择波特率！"] = ".同じボーレートの機器がひとつのシリアルポートに設定されています！";
catalog["后台通讯忙，请稍后重试！"] = "バックグラウンド通信がビジーです。再試行してください！";
catalog["提示：设备连接成功，但获取设备扩展参数失败"] = "機器接続成功が、拡張パラメータ設定が失敗しました";
catalog["，继续添加？"] = "追加を続行しますか？";
catalog["提示：设备连接成功，但控制器类型与实际不符，将修改为"] = "機器接続成功しましたが、制御盤タイプがことなるので、修正しました ";
catalog["门控制器，继续添加？"] = "(s)ドア制御盤。追加続行しますか？";
catalog["一体机，继续添加？"] = "アクセスコントロール機器。追加続行しますか？";
catalog["提示：设备连接成功，确定后将添加设备！"] = "機器接続成功。制御盤タイプも一致しましたので、確認後追加します！";
catalog["提示：设备连接失败（错误码："] = "機器接続失敗（エラーコード：";
catalog["），确定添加该设备？"] = "），この機器を追加しますか？";
catalog["提示：设备连接失败（原因："] = "機器接続失敗（原因： ";
catalog["您选择了[新增时删除设备中数据]，系统将自动删除设备中的数据(事件记录除外)，确定要继续？"] = "確認してください[機器内設定をクリアして追加します]，システムは自動で機器内設定をクリアします(イベントログ以外)，続行しますか？";
catalog["您没有选择[新增时删除设备中数据]，该功能仅用于系统功能演示和测试。请及时手动同步数据到设备，以确保系统中和设备中权限一致，确定要继续？"] = "確認してください[機器内設定をクリアして追加します]，この機能はシステムのテストまたは、デモに使用します。ソフトウェアと機器を手動で同期してください。続行しますか？";
catalog["编辑设备信息("] = "機器情報";
catalog["对不起，您没有访问该页面的权限，不能浏览更多信息！"] = "このページの閲覧権限がありません！";
//in file--D:\trunk\units\adms\mysite\iclock\templates\Dev_RTMonitor.html
catalog["确定要清除命令队列？"] = "コマンドをクリアしますか？";
catalog["清除缓存命令成功！请及时手动同步数据到设备，以确保系统中和设备中权限一致！"] = "コマンドクリア成功！ソフトウェアと機器を同期させてください！";
catalog["清除缓存命令失败!"] = "キャッシュコマンドクリア失敗!";
//in file--D:\trunk\units\adms\mysite\att\templates\att_USER_OF_RUN.html
catalog["员工排班表"] = "ユーザースケジュールテーブル";
catalog["临时排班表"] = "臨時スケジュールテーブル";
catalog["排班时间段详细明细"] = "シフトスケジュールタイムテーブル詳細";
catalog["排班时间段详细明细(仅显示三个月)"] = "シフトスケジュールタイムテーブル詳細(3か月間のみ)";
catalog["排班时间段详细明细(仅显示到年底)"] = "シフトスケジュールタイムテーブル詳細(年末まで)";
//in file--D:\trunk\units\adms\mysite\att\templates\NUM_RUN_edit.html
catalog["请选择时段"] = "シフトタイムスケジュール選択";
catalog["选择日期"] = "日付選択";
catalog["第"] = "No.";
catalog["天"] = "日";
catalog["周的周期不能大于52周"] = "週間周期は52週を超えることはできません";
catalog["月的周期不能大于12个月"] = "月間周期は12か月を超えることはできません";
catalog["第"]="No.";
catalog["天"] = "日";
//in file--D:\trunk\units\adms\mysite\att\templates\NUM_RUN_list.html
catalog["时间段明细"] = "シフトタイムテーブル詳細";
catalog["确定删除该时段吗？"] = "シフトタイムテーブルを削除しますか？";
catalog["操作失败 {0} : {1}"] = "操作失敗 {0} : {1}";
//in file--D:\trunk\units\adms\mysite\att\templates\NUM_RUN_opform_OpAddTimeTable.html
catalog["已选择"] = "選択";
//in file--D:\trunk\units\adms\mysite\att\templates\USER_OF_RUN_opform_OpAddTempShifts.html
catalog["日期格式输入错误"] = "日付形式は不正です！";
catalog["日期格式不正确！"] = "日付形式は不正です！"
catalog["夏令时名称不能为空！"] = "夏時間名は空白にできません！"
catalog["起始时间不能和结束时间相等！"] = "開始時間は、終了時間と同じにできません！";
//in file--D:\trunk\units\adms\mysite\att\templates\USER_OF_RUN_opform_OpAddUserOfRun.html
catalog["请选择一个班次"] = "シフト選択";
catalog["结束日期不能小于开始日期!"] = "終了日は開始日より早くてはいけません!";
catalog["请输入开始日期和结束日期! "] = "開始日と終了日を入力してください!";
catalog["只能设置一个班次! "] = "1つのシフトのみ設定可能です!";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccAntiBack_edit.html
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行反潜设置！"] = "選択した機器には、アンチ・パスバックは設定できません！";
catalog["读取到错误的设备信息，请重试！"] = "不正機器情報がリードされました。再試行してください！";
catalog["或"] = " または ";
catalog["反潜"] = " アンチ・パスバック";
catalog["读头间反潜"] = "リーダ間アンチ・パスバック";
catalog["反潜"] = " アンチパスバック";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccAntiBack_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccDoor_edit.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccFirstOpen_edit.html
catalog["当前门:"] = "選択ドア:";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccFirstOpen_list.html
catalog["删除开门人员"] = "ユーザー削除";
catalog["请先选择要删除的人员！"] = "最初にユーザーを選択して、削除してください！";
catalog["确认要从首卡常开设置信息中删除开门人员？"] = "連続解錠ユーザー情報から、ユーザーを削除しますか？";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccFirstOpen_opform_OpAddEmpToFCOpen.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccInterLock_edit.html
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行互锁设置！"] = "選択した機器に、インターロックは設定できません！";
catalog["门:"] = "ドア: ";
catalog["与"] = "and";
catalog["互锁"] = " インターロック";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccInterLock_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLevelSet_list.html
catalog["数据下载进度"] = "データダウンロード処理";
catalog["设备名称"] = "機器名";
catalog["总进度"] = "全処理";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLevelSet_opform_OpAddEmpToLevel.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLinkageIO_edit.html
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行联动设置！"] = "選択した機器に、出力設定はできません！";
catalog["请输入联动设置名称！"] = "出力設定名を入力してください！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLinkageIO_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMap_edit.html
catalog["请选择地图！"] = "マップを選択して下さい！";
catalog["图片格式无效！"] = "不正写真形式！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardEmpGroup_list.html
catalog["浏览多卡开门人员组："] = "マルチパーソングループ閲覧：";
catalog[" 的人员"] = " メンバー";
catalog["当前不存在多卡开门人员组"] = "現在マルチパーソングループはありません";
catalog["删除人员"] = "ユーザー削除";
catalog["确认要从多卡开门人员组中删除人员？"] = "マルチパーソングループから、ユーザーを削除しますか？";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardEmpGroup_opform_OpAddEmpToMCEGroup.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardSet_edit.html
catalog["请至少在一个组内填入开门人数！"] = "1グループのユーザー数を入力してください！";
catalog["至少两人同时开门！"] = "2人認証で解錠できます！";
catalog["最多五人同时开门！"] = "最大5人認証で解錠できます！";
catalog["人"] = "ユーザー";
catalog["您还没有设置多卡开门人员组！请先添加！"] = "マルチパーソンユーザーグループが未設定です！最初に設定してください！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardSet_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccTimeSeg_edit.html
catalog["请在文本框内输入有效的时间！"] = "解錠時間を入力してください！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccWiegandFmt_list.html
catalog["对不起,您没有韦根卡格式设置的权限,不能进行当前操作！"] = "この操作の権限がありません！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Door_Mng.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Door_Set.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Electro_Map.html
catalog["添加门到当前地图"] = "マップにドアを追加します";
catalog["请选择要添加的门！"] = "ドアを選択して追加してください！";
catalog["确定要删除当前电子地图："] = "マップを削除することを確認してください： ";
catalog["添加辅助点到当前地图"] = "補助入出力をマップに追加します";
catalog["请选择要添加的辅助点！"] = "補助入出力を選択して追加してください！";

//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_EmpLevel_Byemp.html
catalog["浏览人员："] = "ユーザー閲覧：";
catalog[" 所属权限组"] = " アクセスレベル";
catalog["当前不存在人员"] = "ユーザーが存在しません";
catalog["删除所属权限组"] = "アクセスレベル削除";
catalog["请先选择要删除的权限组！"] = "アクセスレベルを選択してから削除してください！";
catalog["确认要删除人员所属权限组？"] = "アクセスレベルを削除しますか？";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_EmpLevel_Bylevel.html
catalog["数据处理进度"] = "データ処理";
catalog[" 的开门人员"] = " ユーザー";
catalog["当前不存在权限组"] = "アクセスレベルが存在しません";
catalog["从权限组中删除"] = "アクセスレベル削除";
catalog["权限组列表"]="アクセスレベルリスト";
catalog["门列表"]="ドアリスト"
catalog["人员列表"]="ユーザーリスト"
catalog["浏览 "]="閲覧 "
catalog["可以进出的门"]=" アクセス権限があります"
catalog["当前不存在人员"]="ユーザー無"
catalog["以人员查询"]="ユーザーにより"
catalog["以门查询"]="ドアにより "
catalog["以权限组查询"]="アクセスレベルにより"
catalog["确认要从权限组中删除人员？"] = "アクセスレベルからユーザーを削除しますか？";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Monitor_All.html
catalog["远程开门"] = "Remote 遠隔解錠";
catalog["选择开门方式"] = "解錠モード選択";
catalog["开门："] = "解錠のために：";
catalog[" 秒"] = " 秒(s)";
catalog["常开"] = "解錠";
catalog["启用当天常开时间段"] = "自動解錠モードタイムゾーン有効";
catalog["远程关门"] = "遠隔施錠";
catalog["选择关门方式"] = "施錠モード選択";
catalog["关门"] = "施錠";
catalog["禁用当天常开时间段"] = "自動解錠モードタイムゾーン無効";
catalog["当前门处于常开状态，是否禁用当天常开时间段后关门？"] = "選択ドアの、自動解錠モードタイムゾーンを無効にしますか？";
catalog["当前已常开"] = "解錠";
catalog["发送请求失败！"] = "送信失敗！";
catalog["发送请求成功！"] = "送信成功！";
catalog["发送请求失败，请重试！"] = "送信失敗，再試行してください！";
catalog["当前没有符合条件的门！"] = "条件を満たすドアがありません！";
catalog["请输入有效的开门时长！必须为1-254间的整数！"] = "ドア解錠時間を1-254の整数で入力してください！";
catalog["禁用"] = "無効";
catalog["离线"] = "オフライン";
catalog["报警"] = "アラーム";
catalog["门开超时"] = "開扉タイムアウト";
catalog["关闭"] = "閉扉";
catalog["打开"] = "開扉";
catalog["无门磁"] = "ドアセンサー無";
catalog["当前设备状态不支持该操作！"] = "選択した機器で、この操作はサポートされていません！";
catalog["该人员没有登记照片！"] = "写真無！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform_alarm.html
catalog["导出报表"] = "レポートエクスポート";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform_allevent.html
catalog["设置定时获取记录时间"] = "履歴取得時間設定";
catalog["每天"] = "履歴取得  ";//特殊翻译请核对页面
catalog[" 点自动从设备获取新记录"] = " 毎日自動的";
catalog["注：请确保服务器在设置的时间点处于开机状态。"] = "注意：サーバが設定した時間に起動していることを確認してください。";
catalog["定时下载记录时间设置成功！该设置将在软件服务或者操作系统重启后生效！"] = "時間設定成功！設定はコンピュータの再起動後に有効になります！";
catalog["定时下载记录事件设置失败！请重试！"] = "時間設定失敗！再試行してください！";
catalog["请输入有效的时间点(0-23)！"] = "有効な時間を入力してください(0-23)！";
catalog["无"] = "無";
catalog["注：1.请确保服务器在设置的时间点处于开机状态。<br/> 2.如需设置多个时间点，请以逗号分开。"] = "注意：1.サーバが設定時間に起動していることを確認してください。<br/> 2.複数時間を設定する場合はカンマで区切ってください。";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform_emplevel.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Device_opform_OpChangeIPOfACPanel.html
catalog["请输入有效的IPv4地址！"] = "IPv4アドレスを入力してください！";
catalog["请输入有效的网关地址！"] = "ゲートウェイアドレスを入力してください！";
catalog["请输入有效的子网掩码！"] = "サブネットマスクを入力してください！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Device_opform_OpCtrlAuxOut.html
catalog["获取设备扩展参数失败，当前操作不可用！"] = "選択した機器で、この操作はサポートされていません！";
catalog["请选择要关闭的辅助输出点！"] = "閉じたい補助出力ポートを確認してください！";
catalog["请选择辅助输出点！"] = "補助出力点を選択 ！";
catalog["请输入正确的时间！"] = "正しい時刻を入力してください ！";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Device_opform_OpSearchACPanel.html
catalog["退出"] = "退出";
catalog["正在搜索中,请等待!"] = "検索中。しばらくお待ちください!";
catalog["当前共搜索到的门禁控制器总数为："] = "検索されたアクセスコントロール機器数：";
catalog["自定义设备名称"] = "機器名";
catalog["新增时删除设备中数据"] = "機器内データクリア後追加";
catalog["设备名称不能为空，请重新添加设备！"] = "機器名は空白にできません。再度機器を追加してください！";
catalog["的设备添加成功！"] = " 機器追加成功！";
catalog["已添加设备数："] = "追加済機器数：";
catalog["IP地址："] = "IPアドレス：";
catalog[" 已存在！"] = "既に存在します！";
catalog["序列号："] = "シリアルナンバー";
catalog["IP地址为："] = "IPアドレス：";
catalog[" 的设备添加失败！原因："] = " 追加失敗！原因： ";
catalog[" 的设备添加异常！原因："] = " 機器追加異常！原因： ";
catalog["的设备添加成功，但设备扩展参数获取失败！原因："] = " 機器追加は成功しましたが、拡張パラメータ設定が失敗しました！原因：";
catalog["设备连接成功，但无数据返回，添加设备失败！"] = "機器接続は成功しましたが、データ返信がありませんので、追加できません！";
catalog["设备连接失败(错误码："] = "機器接続失敗(エラーコード： ";
catalog[")，无法添加该设备！"] = ")，追加失敗！";
catalog["设备连接失败(原因："] = "機器接続失敗(原因：";
catalog["修改设备IP地址"] = "IPアドレス変更";
catalog["原IP地址"] = "現IPアドレス";
catalog["新IP地址"] = "新IPアドレス";
catalog["网关地址"] = "ゲートウェイアドレス";
catalog["子网掩码"] = "サブネットマスク";
catalog["请输入设备通讯密码:"] = "通信パスワード入力:";
catalog["新的IP地址不能为空！"] = "新IPアドレスは空白にできません！";
catalog["请输入一个有效的IPv4地址！"] = "Pv4アドレスを入力してください！";
catalog["请输入一个有效的网关地址！"] = "ゲートウェイアドレスを入力してください！";
catalog["请输入一个有效的子网掩码！"] = "サブネットマスクを入力してください！";
catalog["该IP地址的设备已存在或该IP地址已被使用，不能添加！请重新输入！"] = "このIPアドレスは既に使用中です。再入力してください！";
catalog["操作失败！原因："] = "操作失敗！原因：";
catalog["设备连接成功，但修改IP地址失败！"] = "機器接続は成功しましたが、IPアドレス変更が失敗しました！";
catalog["设备连接失败，故修改IP地址失败！"] = "機器接続失敗！";
catalog["没有搜索到门禁控制器！"] = "アクセスコントロール機器が見つかりません！";
//in file--D:\trunk\units\adms\mysite\personnel\templates\Department_list.html
catalog["显示部门树"] = "部署階層閲覧";
catalog["隐藏部门树"] = "部署階層非表示";
//in file--D:\trunk\units\adms\mysite\personnel\templates\EmpChange_edit.html
catalog["请选择一个调动栏位"] = "転送先を選択して下さい";
//in file--D:\trunk\units\adms\mysite\personnel\templates\EmpItemDefine_list.html
catalog["部门花名册"] = "部署権限";
catalog["学历构成分析表"] = "出身校表";
catalog["人员流动表"] = "ユーザー売上表";
catalog["人员卡片清单"] = "ユーザーカードリスト";
catalog["请选择开始日期和结束日期"] = "開始日と終了日を選択して下さい";
catalog["开始日期不能大于结束日期"] = "開始日は、終了日より遅くてはなりません";
//in file--D:\trunk\units\adms\mysite\personnel\templates\Employee_edit.html
catalog["图片格式无效!"] = "不正写真型式!";
catalog["人员编号必须为数字"] = "ユーザーNoは数値です";
catalog["请输入有效的E_mail!"]="E_mailを入力してください!";
catalog["身份证号码不正确"] = "不正IDカードNo";
catalog["没有可选的门禁权限组！"] = "アクセスレベルがありません！";
catalog["指纹模板错误，请立即联系开发人员！"] = "指紋テンプレートエラー。管理者に連絡してください！";
catalog["指纹模板错误，请重新登记！"] = "指紋テンプレートエラー。再登録してください！";

catalog["修改密码"] = "パスワード変更";
catalog["旧密码："] = "旧パスワード：";
catalog["新密码："] = "新パスワード：";
catalog["确认密码："] = "パスワード確認：";
catalog["最大6位整数"] ="最大6桁整数";

//in file--D:\trunk\units\adms\mysite\personnel\templates\Employee_list.html
//in file--D:\trunk\units\adms\mysite\personnel\templates\Employee_opform_OpAddLevelToEmp.html
//in file--D:\trunk\units\adms\mysite\personnel\templates\IssueCard_opform_OpBatchIssueCard.html
catalog["每次发卡数量不能超过100"] = "100枚以上のカードは一度に発行できません";
catalog["起始编号长度不能超过"] = "開始番号が不正です ";
catalog["位"] = " 桁";
catalog["结束编号长度不能超过"] = "終了番号が不正です";
catalog["起始人员编号与结束人员编号的长度位数不同！"] = "開始番号と終了番号の長さが異なります！";
//in file--D:\trunk\units\adms\mysite\personnel\templates\LeaveLog_list.html
//in file--D:\trunk\units\adms\mysite\worktable\templates\worktable_common_monitor.html
catalog["点击查看消息详情"] = "クリックで、ビューメッセージ詳細表示";
catalog["删除该消息"] = "メッセージ削除";
catalog["公告详情"] = "注意詳細";
//in file--D:\trunk\units\adms\mysite\worktable\templates\worktable_common_opt.html
catalog["保存成功!"] = "保存成功!";
catalog["人员选择:"] = "ユーザー選択:";
//in file--D:\trunk\units\adms\mysite\worktable\templates\worktable_common_search.html
catalog["人员查询"] = "ユーザークエリ";
catalog["人员编号"] = "ユーザーNo";
catalog["姓名"] = "名前";
catalog["身份证号查询"] = "IDカードNoクエリ";
catalog["身份证号码"] = "IDカードNo";
catalog["考勤设备查询"] = "勤怠機器クエリ";
catalog["离职人员查询"] = "退場ユーザークエリ";
catalog["考勤原始数据查询"] = "基本勤怠データクエリ";
catalog["员工调动查询"] = "ユーザー移動クエリ";
catalog["卡片查询"] = "カードクエリ";
catalog["卡号"] = "カードコード";
catalog["部门查询"] = "部署クエリ";
catalog["部门编号"] = "部署番号";
catalog["部门名称"] = "部署名";
catalog["补签卡查询"] = "ログクエリ";
catalog["服务器加载数据失败,请重试!"] = "データロード失敗。再試行してください!";
//in file--D:\trunk\units\adms\mysite\media\jslib\calculate.js
catalog["补签卡"] = "ログ";
catalog["补请假"] = "リーブ";
catalog["新增排班"] = "スケジュール追加";
catalog["临时排班"] = "臨時スケジュール";
catalog["结束日期不能大于今天"] = "終了日は今日より後";
catalog["统计只能当月日期，或者天数不能超过开始日期的月份天数！ "] = "集計はその月の日付のみ含みます！ ";
catalog["统统计的时间可能会较长，请耐心等待"] = "集計処理は時間がかかります";
catalog["请选择人员或部门"] = "ユーザーか部署を選択して下さい";
catalog["统计结果详情"] = "集計結果";
catalog["每日考勤统计表"] = "日集計テーブル";
catalog["考勤明细表"] = "勤怠詳細";
catalog["请假明细表"] = "リーブ詳細";
catalog["考勤统计汇总表"] = "集計サマリー";
catalog["原始记录表"] = "勤怠ログテーブル";
catalog["补签卡表"] = "ログテーブル";
catalog["请假汇总表"] = "リーブサマリー";
catalog["请选择开始日期或结束日期!"] = "開始日と終了日を選択して下さい!";
catalog["开始日期不能大于结束日期!"] = "開始日は終了日より遅くてはいけません!";
catalog["最多只能查询31天的数据!"] = "31日までのデータを照会できます!";
catalog["请在查询结果中选择人员！"] = "クエリリストからユーザーを選択して下さい！";
catalog["取消"] = "戻る";
//in file--D:\trunk\units\adms\mysite\media\jslib\CDrag.js
catalog["展开"] = "展開";
catalog["收缩"] = "閉じる";
catalog["自定义工作面板"] = "ワークパネルカスタマイズ";
catalog["锁定"] = "施錠";
catalog["解除"] = "解錠";
catalog["常用操作"] = "通常操作";
catalog["常用查询"] = "通常クエリ";
catalog["考勤快速上手"] = "勤怠クイックスタート";
catalog["门禁快速上手"] = "アクセスコントロールクイックスタート";
catalog["系统提醒、公告"] = "システム注意と通知";
catalog["人力构成分析"] = "ユーザー構成分析";
catalog["最近门禁异常事件"] = "最近例外アクセスコントロール";
catalog["本日出勤率"] = "本日出勤率";
catalog["加载中......"] = "ロード中......";
//in file--D:\trunk\units\adms\mysite\media\jslib\datalist.js
catalog["是否"] = "はい/いいえ";
catalog["选择所有 {0}(s)"] = "全て選択 {0}(s)";
catalog["选择 {0}(s): "] = "選択 {0}(s):";
catalog["服务器处理数据失败，请重试！"] = "サーバデータ処理失敗。再試行してください！";
catalog["新建相关数据"] = "対応データ作成";
catalog["浏览相关数据"] = "対応データ閲覧";
catalog["添加"] = "追加";
catalog["浏览"] = "閲覧";
catalog["编辑"] = "編集";
catalog["编辑这行数据"] = "列編集 ";
catalog["升序"] = "昇順";
catalog["降序"] = "降順";
//in file--D:\trunk\units\adms\mysite\media\jslib\datalistadd.js
catalog["该模型不支持高级查询功能"] = "この機器は、拡張クエリをサポートしていません";
catalog["高级查询"] = "拡張クエリ";
catalog["导入"] = "インポート";
catalog["请选择一个上传的文件!"] = "アップロードするファイルを選択してください!";
catalog["标题行号必须是数字!"] = "タイトル列は数値です!";
catalog["记录行号必须是数字!"] = "入場記録列は数値です!";
catalog["请选择xls文件!"] = "xlsファイルを選択してください!";
catalog["请选择csv文件或者txt文件!"] = "csvまたは、txtファイルを選択してください!";
catalog["文件标头"] = "ファイルヘッダー";
catalog["文件记录"] = "ファイルレコード";
catalog["表字段"] = "テーブルフィールド";
catalog["请先上传文件！"] = "最初にファイルをアップロードしてください！";
catalog["导出"] = "エクスポート";
catalog["页记录数只能为数字"] = "ページエントリー数は数値です";
catalog["页码只能为数字"] = "ページ番号は数値のみです";
catalog["记录数只能为数字"] = "入場記録は数字のみです";
catalog["用户名"] = "ユーザー名";
catalog["动作标志"] = "アクションフラグ";
catalog["增加"] = "追加";
catalog["修改"] = "編集";
catalog["删除"] = "削除";
catalog["其他"] = "その他";
//in file--D:\trunk\units\adms\mysite\media\jslib\electro_map.js
catalog["地图宽度到达上限(1120px)，不能再放大！"] = "地図幅上限(1120px)，放大できません！";
catalog["地图宽度到达下限(400px)，不能再缩小！"] = "地図幅下限(400px)，縮小できません！";
catalog["地图高度到达下限(100px)，不能再缩小！"] = "地図高さ下限(100px)，縮小できません！";
catalog["门图标的位置（Top或Left）到达下限，请稍作调整后再进行缩小操作！"] = "ドアアイコン位置（上または左）が下限に達しました。調整してください！";

//in file--D:\trunk\units\adms\mysite\media\jslib\importAndExport.js
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.plus.js
catalog["信息提示"] = "Tips";
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.plus.js
catalog["日期"] = "日付";
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.zcommon.js
catalog["标签页不能多于6个!"] = "6タブ以下にしてください!";
catalog["按部门查找"] = "部署検索";
catalog["选择部门下所有人员"] = "部署内全ユーザー選択";
catalog["(该部门下面的人员已经全部选择!)"] = "(部署内全ユーザーが選択されました!)";
catalog["按人员编号/姓名查找"] = "ユーザー検索　No/名前";
catalog["按照人员编号或姓名查找"] = "ユーザー選択 No/名前";
catalog["查询"] = "クエリ";
catalog["请选择部门"] = "部署選択";
catalog["该部门下面的人员已经全部选择!"] = "部署内全ユーザーが選択されました!";
catalog["打开选人框"] = "選択ボックスを開く";
catalog["收起"] = "閉じる";
catalog["已选择人员"] = "ユーザー選択";
catalog["清除"] = "クリア";
catalog["编辑还未完成，已临时保存，是否取消临时保存?"] = "編集は未完成で一時的に保存されます。保存をキャンセルしますか?";
catalog["恢复"] = "リストア";
catalog["会话已经过期或者权限不够,请重新登入!"] = "セッションは終了したか、権限がありません。再施行してください!";
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.zgrid.js
catalog["没有选择要操作的对象"] = "操作対象がありません";
catalog["进行该操作只能选择一个对象"] = "この操作では、１つのオブジェクトのみ選択できます";
catalog["相关操作"] = "関連操作";
catalog["共"] = "トータル";
catalog["记录"] = "記録";
catalog["页"] = "ページ";
catalog["首页"] = "最初";
catalog["前一页"] = "前へ";
catalog["后一页"] = "次へ";
catalog["最后一页"] = "最後";
catalog["选择全部"] = "全て";
//in file--D:\trunk\units\adms\mysite\media\jslib\widgets.js
catalog["January February March April May June July August September October November December"] = "1月 2月 3月 4月 5月 6月 7月 8月 9月 10月 11月 12月";
catalog["S M T W T F S"] = "日 月 火 水 木 金 土";
//---------------------------------------------------------
catalog["记录条数不能超过10000"] = "the max 10000";
catalog["请输入大于0的数字"] = "0より大きい数字を入力してください";
catalog["当天存在员工排班时"] = "現在の日にスケジュールを持ちます";

catalog["暂无提醒及公告信息"] = "注意と通知はありません";
catalog["关于"] = "About ";
catalog["版本号"] = "バージョンNo";
catalog["产品ID"] = "プロダクトID";
catalog["本系统建议使用浏览器"] = "推奨ブラウザ";
catalog["显示器分辨率"] = "モニター解像度";
catalog["及以上像素"] = "画素数";
catalog["软件运行环境"] = "ソフトウェア実行環境";
catalog["系统默认"] = "デフォルト";

catalog["photo"] = "写真";
catalog["table"] = "テーブル";

catalog["此卡已添加！"] = "このカードは追加済みです！";
catalog["卡号不正确！"] = "カードNoが不正です！";
catalog["请输入要添加的卡号！"] = "カードNoを入力してください！";
catalog["请选择刷卡位置！"] = "カード読取方法を選択してください！";
catalog["请选择人员！"] = "ユーザー選択！";
catalog["table"] = "テーブル";
catalog["table"] = "テーブル";
catalog["首字符不能为空!"]="最初の文字は空白にできません!";
catalog["密码长度必须大于4位!"]="パスワードは4桁以下です!";

catalog["当前列表中没有卡可供分配！"] = "現在のリストにカードを登録できます！";
catalog["当前列表中没有人员需要分配！"] = "現在のリストにユーザーがありません！";
catalog["没有已分配人员！"] = "登録ユーザーはいません！";
catalog["请先点击停止读取！"] = "最初にカード読取を停止してください！";
catalog["请选择需要分配的人员！"] = "カードを割り当てたいユーザーを選択してください！";

catalog["请选择一个介于1到223之间的数值！"] = "1～223の値を指定してください！";
catalog["备份路径不存在，是否自动创建？"] = "バックアップ先が存在しません。自動で作成しますか？";
catalog["处理中"] = "処理中"
catalog["是"] = "はい"
catalog["否"] = "いいえ"
//------------------------------------------------------------------------
//in file--D:\trunk\units\adms\mysite\media\jslib\worktable.js
catalog["已登记指纹"] = "通信パスワード"
//人员判断哪里 验证 输入不合法
catalog["不合法"] = "不正";

catalog["通讯密码"] = "通信パスワード";

catalog["登记指纹功能只支持IE浏览器"] = "この機能はIEブラウザのみサポートされます";

catalog["请安装指纹仪驱动"] = "指紋リーダドライバをインストールしてください";

catalog["解析xml文件出错"] = "xmlファイルロード";

catalog["该通道已达最大访问量！"] = "チャンネルのビジター数が最大に達しました！";

catalog["当前没有可用的角色,请先添加角色"] = "現在選択可能な権限はありません。最初に1つ以上の権限を作成してください";

catalog["当前设备IP地址和服务器不在同一网段，请先将其调整到一个网段，再尝试添加！"] = "機器とサーバが、異なるセグメントです。同じネットワークセグメントに設定してください！";

catalog["数据库将备份到:"]="データベースはバックアップされるでしょう:";

//
catalog["所选的部门总数不能大于2000"]="2000以上の部署は選択できません";

catalog["操作成功！"] = "操作成功！";
catalog["操作失败！"] = "操作失敗！";
catalog["服务器处理数据失败，请重试！错误码："] = "サーバはデータ処理を失敗しました。再施行してください！エラーコード：";
catalog["重连间隔时间必须为整数！"] = "再接続間隔は数値です！";
catalog["设置成功，重启服务后生效！"]="設定成功。設定はサーバおよびソフトウェアの再起動後、有効になります！";
catalog["设置成功！"]="設定成功！";

//catalog["保存参数成功！"] = "保存成功！";
catalog["获取记录时间点不能为空！"] = "履歴取得時間は、空白にできません！";

catalog["用户注册失败，请检查设备配置"] = "ユーザー登録失敗。機器設定を確認してください";
catalog["目前该功能仅支持IE系列及IE内核的浏览器，请更换！"] = "この機能は、IEブラウザのみサポートしています！";
catalog["请选择视频设备！"] = "機器を選択してください！";
catalog["控件初始化失败，请确定视频设备类型是否选择正确或重装控件！"] = "ocx初期化失敗。機器タイプをチェックするかocxを再インストールしてください！";
catalog["预览失败"] = "プレビュー失敗";

catalog["邮箱地址格式不正确"] = "不正メールボックスアドレス";
catalog["请输入邮箱地址"] = "E-mailアドレスと入力してください";
catalog["邮件通知"] = "Email通知";
catalog["报警监控"] = "アラームモニタリング";
catalog["辅助输入"] = "補助入力";
catalog["辅助输出"] = "補助出力";
catalog["邮件通知"] = "Email通知";
catalog["请输入邮箱地址"] = "Emailアドレスを入力してください";
catalog["请输入邮箱地址，多个地址用 ';' 隔开"] = "Emailアドレスを入力してください。 ';'";
catalog["邮件发送成功!"] = "メール送信成功!";
catalog["邮件发送失败!"] = "メール送信失敗!";
catalog["邮件发送失败,门禁参数配置中邮箱配置错误!"] = "メール送信失敗。機器メールボックス設定エラー!";
catalog["请选择报警设备!"] = "アラーム機器を選択してください!";

catalog["门状态"] = "ドアステータス";
catalog["门锁状态"] = "ドア位置";
catalog["报警类型"] = "アラームタイプ";
catalog["门关报警"] = "ドア閉扉とアラーム";
catalog["门开报警"] = "ドア開扉とアラーム";
catalog["门开超时"] = "開放タイムアウト";
catalog["解锁"] = "解錠";
catalog["锁定"] = "施錠";
catalog["没有报警"] = "無";
catalog["防拆"] = "タンパー";
catalog["胁迫密码开门"] = "警報パスワード解錠";
catalog["门被意外打开"] = "強制解錠";
catalog["请先关闭门！"] = "最初にドアを選択してください！";
catalog["胁迫开门"] = "警報解錠";
catalog["胁迫指纹开门"] = "警報指紋解錠";

//in file--D:\trunk\units\adms\mysite\ Acc_Reportform.html
catalog["视频服务器登录失败，请确认后重试！原因："] = "ビデオサーバログイン失敗。チェックして再施行してください！原因： ";
catalog["视频服务器登录失败，请确认后重试！错误码："] = "ビデオサーバログイン失敗。チェックして再施行してください！エラーコード： ";
catalog["视频回放失败，请确认后重试！原因："] = "ビデオ再生失敗。チェックして再施行してください！原因：";
catalog["视频回放失败，请确认后重试！错误码："] = "ビデオサーバログイン失敗。チェックして再施行してください！エラーコード： ";
catalog["视频服务器登录失败，请确认后重试！"] = "ビデオサーバログイン失敗。チェックして再施行してください！"
//视频模块国际化-start
catalog["当前系统中没有添加视频服务器，请添加！"] = "システムにビデオサーバが存在しません。最初に設定してください！";
catalog["视频通道不能重复选择，请重新选择！"] = "ビデオチャンネルが見つかりません。再選択してください！";
catalog["读头"] = "リーダ";
catalog["名称"] = "名称";
catalog["视频时长不能小于0，请输入正确的视频时长!"] = "ビデオ表示間隔は0秒以下にはできません。正しい値を入力してください!";
catalog["录像时长不能小于0，请输入正确的录像时长!"] = "ビデオ録画間隔は0秒以下にできません。正しい値を入力してください!";
catalog["添加摄像机到当前地图"] = "マップにカメラ追加";
catalog["请选择要添加的摄像头！"] = "追加したいカメラを選択してください！";
catalog["视频查询"] = "ビデオ検索";
catalog["视频联动"] = "ビデオ出力";
catalog["视频加载中，请稍侯......"] = "ビデオロード中。お待ちください......";
catalog["该通道已达最大访问量或视频服务器未连接!"] = "チャンネルが最大数に達したか、ビデオサーバが未接続です!";
catalog["预览失败，请确认后重试！原因："] = "プレビュー失敗。再施行してください！原因：";
catalog["预览失败，请确认后重试！错误码："] = "プレビュー失敗。再施行してください！エラーコード：";
catalog["无此权限！"] = "権限がありません！";
catalog["没有录像文件！"] = "ビデオファイル無し！";
catalog["该通道已达最大访问量或视频服务器未连接！"] = "チャンネルが最大数に達したか、ビデオサーバが未接続です！";
catalog["从视频服务器导出失败！"] = "ビデオサーバからエクスポート失敗！";
catalog["从视频服务器导出成功！"] = "ビデオサーバからエクスポート成功！";
catalog["视频弹出窗口高度必须为整数！"] = "ビデオポップアップ画面の高さは整数です！";
catalog["请选择需要设置的对象!"] = "設定したいオブジェクトを選択してください!";
//海康dvr last_error
catalog["HIKVISION_ERROR_1"] = "不正ユーザーパスワード.";
catalog["HIKVISION_ERROR_4"] = "不正チャンネル No.";
catalog["HIKVISION_ERROR_5"] = "接続可能DVRクライアント数が超過しました.";
catalog["HIKVISION_ERROR_7"] = "DVR接続失敗.";
catalog["HIKVISION_ERROR_8"] = "DVRにデータ送信失敗.";
catalog["HIKVISION_ERROR_10"] = "DVRよりデータ受信失敗.";
catalog["HIKVISION_ERROR_17"] = "不正パラメータ.";
catalog["HIKVISION_ERROR_19"] = "HD無.";
catalog["HIKVISION_ERROR_20"] = "HDエラー.";
catalog["HIKVISION_ERROR_21"] = "サーバHDディスクがいっぱいです.";
catalog["HIKVISION_ERROR_22"] = "サーバHDエラー.";
catalog["HIKVISION_ERROR_24"] = "サーバがビジー.";
catalog["HIKVISION_ERROR_28"] = "DVRリソース不足.";
catalog["HIKVISION_ERROR_29"] = "不正DVR操作.";
catalog["HIKVISION_ERROR_33"] = "サーバに、指定された再生ファイルが見つかりません.";
catalog["HIKVISION_ERROR_36"] = "最後の操作は終了しませんでした.";
catalog["HIKVISION_ERROR_38"] = "再生エラー.";
catalog["HIKVISION_ERROR_46"] = "最大数です.";
catalog["HIKVISION_ERROR_47"] = "ユーザーが存在しません.";
catalog["HIKVISION_ERROR_52"] = "ユーザーが最大数になりました.";
catalog["HIKVISION_ERROR_74"] = "操作キャンセル.";
catalog["HIKVISION_ERROR_90"] = "機器がバックアップされています.";

catalog["许可信息"] = "ライセンス情報";

catalog["请切换为英文输入法状态！"] = "英語の入力メソッドに変更してください!";

catalog["许可信息"] = "ライセンス情報";
catalog["请选择每个扩展板的继电器数量！"] = "拡張ボードのリレー数を選択してください！";

//登录页面验证
catalog["比对验证中，请稍等!"] = "認証中!";
catalog["验证失败，请重试!"] = "失敗。再施行してください!";
catalog["10.0指纹算法许可失败!"] = "10.0指紋認証アルゴリズムライセンス、認証失敗!";
catalog["验证通过，登录系统!"] = "認証。システムログイン!";
catalog["获取指纹失败，请重试!"] = "この機能は、IEブラウザのみサポートされています";
catalog["登记指纹功能只支持IE浏览器"] = "指紋リーダドライバをインストールしてください";
catalog["请安装指纹仪驱动"] = "Please install Fingerprint Reader Driver";

//访客
catalog["进入地点"] = "入場地点";
catalog["离开地点"] = "退出地点";
catalog["被访人姓名"] = "ユーザー姓";
catalog["被访人姓氏"] = "ユーザー名";
catalog["是否重新打印访客单？"] = "ビジター再登録しますか？";
catalog["没有注册读写器控件，是否下载控件？"] = "リーダコントロールをダウンロードしますか？";
catalog["没有注册扫描仪控件，是否下载控件？"] = "スキャナコントロールをダウンロードしますか？";
catalog["暂时不支持该证件类型！"] = "一時的にドキュメントタイプをサポートできません！";
catalog["请选择正确的证件类型或调整证件的位置！"] = "正しいドキュメントタイプを選択してください！";
catalog["加载核心失败！"] = "ロード失敗！";
catalog["初始化失败！"] = "初期化失敗！";
catalog["请放好身份证！"] = "ユーザーIDを入力してください！";
catalog["没有检测到身份证阅读器！"] = "カードリーダが検出できません！";
catalog["目前该功能仅支持二代身份证！"] = "この機能はサポートされません！";
catalog["没有可选的权限组！"] = "利用可能なレベルがありません！";
catalog["卡号已存在，如果确认将重新发卡，请先清除该卡原持卡人"] = "カードNoは既に存在します。再登録したい場合は、最初に当該カードを削除してください ";

//init_base_frame.js
catalog["正式版许可"] = "正規版";
catalog["试用版许可"] = "試用版";
