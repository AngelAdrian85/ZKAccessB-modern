// -*- coding: utf-8 -*-
___f=function(){
jQuery.validator.messages.required="Requis"
jQuery.validator.messages.email="Pas une adresse mail"
jQuery.validator.messages.date="SVP rentrer date valide: aaaa-mm-jj."
jQuery.validator.messages.dateISO="SVP entrer date(ISO)valide: aaaa-mm-jj."
jQuery.validator.messages.wZBaseDateField="SVP entrer une date valide: aaaa-mm-jj."
jQuery.validator.messages.wZBaseDateTimeField="SVP entrer une date valide: aaaa-mm-jj hh:mm:ss."
jQuery.validator.messages.wZBaseTimeField="SVP entrer eure valide: hh:mm:ss."
jQuery.validator.messages.wZBaseIntegerField="SVP entrer un nombre entier."
jQuery.validator.messages.number="SVP entrer valeur valide."
jQuery.validator.messages.digits="Seulement numérique autorisé"
jQuery.validator.messages.equalTo="Différent"
jQuery.validator.messages.minlength=$.validator.format("au moin {0} Caractères(s)")
jQuery.validator.messages.maxlength=$.validator.format("au plus {0} Caractères(s)")
jQuery.validator.messages.rangelength=$.validator.format("entre {0} et{1} Caractères")
jQuery.validator.messages.range=$.validator.format("Entre {0} et {1}")
jQuery.validator.messages.max=$.validator.format("Veuillez saisir une valeur ne dépassant{0}.")
jQuery.validator.messages.min=$.validator.format("Veuillez entrer une valeur non inférieure à {0}.")
jQuery.validator.messages.xPIN="Seulement numérique ou lettre permis"
jQuery.validator.messages.xNum="Seulement numérique permi"
jQuery.validator.messages.xMobile="Numéro de téléphone mobile erroné"
jQuery.validator.messages.xTele="Numéro de téléphone fixe erroné"
jQuery.validator.messages.xSQL="\" OU \ Pas Permis."
}

___f();

if(typeof(catalog)=="Indéfini") {catalog={}}

//in file--D:\trunk\units\adms\mysite/templates\advenquiry.html
catalog["请选择一个字段"] = "Sil vous plaît sélectionner un champ.";
catalog["'满足任意一个' 值域必须是以','隔开的多个值"] = "Seulement valeur multiple divisé par ',' peut répondre à toute «plage de valeurs";
catalog["输入的值错误"] = "Valeur entrée erronée";
//in file--D:\trunk\units\adms\mysite/templates\base_page_frame.html
catalog["确定注销系统?"] = "Etes-vous sûr de se déconnecter du système?";
catalog["通讯失败"] = "Echec";
catalog["确定"] = "OK";
catalog["确认"] = "OK";
//in file--D:\trunk\units\adms\mysite/templates\data_edit.html
catalog["日志"] = "Connexions";
//in file--D:\trunk\units\adms\mysite/templates\data_list.html
//in file--D:\trunk\units\adms\mysite/templates\DbBackupLog_list.html
catalog["请选择一条历史备份记录!"] = "Sil vous plaît sélectionner une entrée de sauvegarde de lhistoire.";
catalog["还原成功!"] = "Restauré avec succès";
//in file--D:\trunk\units\adms\mysite/templates\DbBackupLog_opform_OpBackupDB.html
catalog["间隔时间不能超过一年"] = "Intervalle ne peut pas dépasser un an.";
catalog["间隔时间不能小于24小时"] = "Intervalle ne peut pas être inférieure à 24 heures.";
catalog["在当前时间的一个小时内只能备份一次"] = "La sauvegarde peut être effectuée quune seule fois à une heure de lheure!";
catalog["请先在服务控制台中设置数据库备份路径"] = "Sil vous plaît définir le chemin de sauvegarde de base de données dans la console de service de première";
//in file--D:\trunk\units\adms\mysite/templates\DbBackupLog_opform_OpInitDB.html
catalog["全部"] = "All";
//in file--D:\trunk\units\adms\mysite/templates\restore.html
catalog["数据格式必须是json格式!"] = "Les données doivent être au format JSON.";
//in file--D:\trunk\units\adms\mysite\iclock\templates\Area_opform_OpAdjustArea.html
catalog["请选择人员!"] = "Sil vous plaît sélectionner une personne!";
catalog["考勤"] = "Présence";
//in file--D:\trunk\units\adms\mysite\iclock\templates\Device_edit.html
catalog["设备名称不能为空"] = "Le nom de périphérique ne peut pas être vide";
catalog["设备序列号不能为空"] = "Le numéro de série de lappareil ne peut pas être vide.";
catalog["通讯密码必须为数字"] = "Le mot de passe de communication doit être un numérique.";
catalog["请输入一个有效的IPv4地址"] = "Veuillez saisir une adresse IPv4 valide.";
catalog["请输入一个有效的IP端口号"] = "Veuillez saisir un numéro de port IP valide.";
catalog["请输入一个RS485地址"] = "Veuillez entrer une adresse RS485.";
catalog["RS485地址必须为1到63之间的数字"] = "Une adresse RS485 doit être un numérique entre 1 et 63.";
catalog["请选择串口号"] = "Sil vous plaît sélectionner un numéro de port série.";
catalog["请选择波特率"] = "Sil vous plaît sélectionner une vitesse de transmission.";
catalog["请选择设备所属区域"] = "Sil vous plaît sélectionner une zone pour le dispositif.";
catalog["串口：COM"] = "Serial port COM";
catalog[" 的RS485地址："] = "Adresse RS485 s";
catalog[" 已被占用！"] = " a été occupé!";
catalog[" 已添加过波特率不为："] = " a ajouté le dispositif pas avec la vitesse de transmission:";
catalog[" 的设备！同一个串口下不允许存在多个波特率不同的设备。请重新选择波特率！"] = ".Sil vous plaît faire en sorte quun port série ne peut exister appareils avec la même vitesse de transmission et de choisir à nouveau la vitesse de transmission!";
catalog["后台通讯忙，请稍后重试！"] = "La communication de fond est occupé, sil vous plaît réessayer plus tard!";
catalog["提示：设备连接成功，但获取设备扩展参数失败"] = "Astuce: Lappareil est connecté avec succès, mais na pas réussi à obtenir les paramètres étendus pour dispositif";
catalog["，继续添加？"] = ",Continuer à ajouter?";
catalog["提示：设备连接成功，但控制器类型与实际不符，将修改为"] = "Astuce: Lappareil est connecté avec succès, mais le type de panneau de contrôle daccès diffère de du réel, modifier pour";
catalog["门控制器，继续添加？"] = "Porte (s) panneau de contrôle. Continuer à ajouter?";
catalog["一体机，继续添加？"] = "Dispositif de contrôle daccès. Continuer à ajouter?";
catalog["提示：设备连接成功，确定后将添加设备！"] = "Astuce: Lappareil est connecté avec succès, et les types des panneaux de contrôle daccès. Ajouter le dispositif après la confirmation!";
catalog["提示：设备连接失败（错误码："] = "Astuce: Le dispositif ne parvient pas à être connecté (code derreur):";
catalog["），确定添加该设备？"] = ").Etes-vous sûr dajouter ce dispositif ?";
catalog["提示：设备连接失败（原因："] = "Astuce: Le dispositif ne parvient pas à être connecté (cause: ";
catalog["您选择了[新增时删除设备中数据]，系统将自动删除设备中的数据(事件记录除外)，确定要继续？"] = "Vous avez vérifié [Effacer les données dans lappareil lors de lajout], le système va automatiquement effacer les données (à lexception du journal des événements) dans le dispositif, assurez-vous de continuer?";
catalog["您没有选择[新增时删除设备中数据]，该功能仅用于系统功能演示和测试。请及时手动同步数据到设备，以确保系统中和设备中权限一致，确定要继续？"] = "Vous avez pas vérifié [Effacer les données dans lappareil lors de lajout], cette fonction est utilisée uniquement pour la démonstration et les essais du système. Sil vous plaît synchroniser les données à lappareil manuellement, afin dassurer la cohérence des niveaux de système et un dispositif, sûr de continuer?";
catalog["编辑设备信息("] = "Informations sur le périphérique dédition";
catalog["对不起，您没有访问该页面的权限，不能浏览更多信息！"] = "Désolé, vous avez pas le droit de visiter cette page, Donc vous ne pouvez pas parcourir plus dinformations!";
//in file--D:\trunk\units\adms\mysite\iclock\templates\Dev_RTMonitor.html
catalog["确定要清除命令队列？"] = "?tes-vous sûr de vouloir effacer commande files dattente?";
catalog["清除缓存命令成功！请及时手动同步数据到设备，以确保系统中和设备中权限一致！"] = "Les commandes de cache sont effacés avec succès! Sil vous plaît synchroniser les données à lappareil manuellement, afin dassurer la cohérence des niveaux dans le système et le dispositif!";
catalog["清除缓存命令失败!"] = "Les commandes de cache ne sont pas effacés avec succès!";
//in file--D:\trunk\units\adms\mysite\att\templates\att_USER_OF_RUN.html
catalog["员工排班表"] = "Tableau planification Personnel";
catalog["临时排班表"] = "Tableau planification temporaire";
catalog["排班时间段详细明细"] = "Planning des détails de fuseau horaire";
catalog["排班时间段详细明细(仅显示三个月)"] = "Les détails de lhoraire de travail (trois mois seulement)";
catalog["排班时间段详细明细(仅显示到年底)"] = "les détails de lhoraire  de travail (uniquement de fin dannée";
//in file--D:\trunk\units\adms\mysite\att\templates\NUM_RUN_edit.html
catalog["请选择时段"] = "Sélectionnez fuseau horaire";
catalog["选择日期"] = "Selectionner date";
catalog["第"] = "No.";
catalog["天"] = "jour";
catalog["周的周期不能大于52周"] = "Une période hebdomadaire ne peut pas dépasser 52 semaines.";
catalog["月的周期不能大于12个月"] = "Une période mensuelle ne peut excéder 12 mois.";
catalog["第"]="No.";
catalog["天"] = "jour";
//in file--D:\trunk\units\adms\mysite\att\templates\NUM_RUN_list.html
catalog["时间段明细"] = "Détails de changement dhoraire";
catalog["确定删除该时段吗？"] = "Etes-vous sûr de vouloir supprimer ce changement dhoraire?";
catalog["操作失败 {0} : {1}"] = "échec de lopération{0} : {1}";
//in file--D:\trunk\units\adms\mysite\att\templates\NUM_RUN_opform_OpAddTimeTable.html
catalog["已选择"] = "selectionné";
//in file--D:\trunk\units\adms\mysite\att\templates\USER_OF_RUN_opform_OpAddTempShifts.html
catalog["日期格式输入错误"] = "Format de date incorrect";
catalog["日期格式不正确！"] = "Le format de la date est erroné!"
catalog["夏令时名称不能为空！"] = "Le nom DST peut pas être nul!"
catalog["起始时间不能和结束时间相等！"] = "Heure de départ ne peut pas être égale à lheure de fin!";
//in file--D:\trunk\units\adms\mysite\att\templates\USER_OF_RUN_opform_OpAddUserOfRun.html
catalog["请选择一个班次"] = "Sélectionnez un changement";
catalog["结束日期不能小于开始日期!"] = "Date de fin ne peut pas être antérieure à la date de début!";
catalog["请输入开始日期和结束日期! "] = "Veuillez saisir la date de début et date de fin.";
catalog["只能设置一个班次! "] = "Vous ne pouvez définir un changement.";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccAntiBack_edit.html
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行反潜设置！"] = "Le périphérique sélectionné actuel ne parvient pas à obtenir des paramètres dextension, réglage de manière antiretour est indisponible pour le disposi.";
catalog["读取到错误的设备信息，请重试！"] = "Informations de périphérique incorrect est lu. Sil vous plaît essayer à nouveau!";
catalog["或"] = " ou ";
catalog["反潜"] = " Anti-retour";
catalog["读头间反潜"] = "Anti-retour entre lecteurs";
catalog["反潜"] = " Anti-retour";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccAntiBack_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccDoor_edit.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccFirstOpen_edit.html
catalog["当前门:"] = "Porte actuelle:";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccFirstOpen_list.html
catalog["删除开门人员"] = "Supprimer une personne douverture";
catalog["请先选择要删除的人员！"] = "Sélectionnez dabord la personne que vous souhaitez supprimer.";
catalog["确认要从首卡常开设置信息中删除开门人员？"] = "?tes-vous sûr de vouloir supprimer la personne douverture de la première carte dinformation de réglage toujours ouverte?";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccFirstOpen_opform_OpAddEmpToFCOpen.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccInterLock_edit.html
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行互锁设置！"] = "Le périphérique sélectionné actuel ne parvient pas à obtenir des paramètres dextension, que le réglage de verrouillage est indisponible pour le dispositif.";
catalog["门:"] = "Porte:  ";
catalog["与"] = "et";
catalog["互锁"] = " Verrouillage";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccInterLock_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLevelSet_list.html
catalog["数据下载进度"] = "La progression du téléchargement de données";
catalog["设备名称"] = "Nom dappareil";
catalog["总进度"] = "Progrès total";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLevelSet_opform_OpAddEmpToLevel.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLinkageIO_edit.html
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行联动设置！"] = "Le périphérique sélectionné actuel ne parvient pas à obtenir des paramètres dextension, pour que le réglage de liaison est indisponible pour le dispositif.";
catalog["请输入联动设置名称！"] = "Veuillez saisir un nom de réglage de liaison.";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccLinkageIO_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMap_edit.html
catalog["请选择地图！"] = "Sil vous plaît choisir la carte!";
catalog["图片格式无效！"] = "Format dimage non valide!";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardEmpGroup_list.html
catalog["浏览多卡开门人员组："] = "Parcourir Multi-Card groupe de personnel douverture:";
catalog[" 的人员"] = " member";
catalog["当前不存在多卡开门人员组"] = "Il ny a pas douverture groupe de personnel actuellement Multi-Carte.";
catalog["删除人员"] = "Supprimer une personne";
catalog["确认要从多卡开门人员组中删除人员？"] = "?tes-vous sûr de vouloir supprimer la personne dans le groupe du personnel douverture multi-cartes?";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardEmpGroup_opform_OpAddEmpToMCEGroup.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardSet_edit.html
catalog["请至少在一个组内填入开门人数！"] = "Veuillez saisir un certain nombre de personnel douverture dans un groupe dau moins.";
catalog["至少两人同时开门！"] = "Au moins deux personnes peuvent ouvrir la porte en même temps!";
catalog["最多五人同时开门！"] = "Dans la plupart des cinq personnes peuvent ouvrir la porte en même temps !";
catalog["人"] = "Personne";
catalog["您还没有设置多卡开门人员组！请先添加！"] = "Vous avez pas fixé de groupe du personnel douverture multi-cartes. Sil vous plaît ajouter une première.";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccMoreCardSet_list.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccTimeSeg_edit.html
catalog["请在文本框内输入有效的时间！"] = "Veuillez saisir le temps valide dans le champ.";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\AccWiegandFmt_list.html
catalog["对不起,您没有韦根卡格式设置的权限,不能进行当前操作！"] = "Désolé, vous avez pas le droit de définir le format de carte Wiegand, et ne pouvez pas effectuer lopération en cours.";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Door_Mng.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Door_Set.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Electro_Map.html
catalog["添加门到当前地图"] = "Ajouter portes sur la carte actuelle";
catalog["请选择要添加的门！"] = "Sil vous plaît choisir les portes que vous souhaitez ajouter!";
catalog["确定要删除当前电子地图："] = "Confirmez que vous allez supprimer la carte actuelle: ";
catalog["添加辅助点到当前地图"] = "Ajouter auxiliaire sur la carte actuelle";
catalog["请选择要添加的辅助点！"] = "Sil vous plaît choisir lauxiliaire que vous souhaitez ajouter!";

//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_EmpLevel_Byemp.html
catalog["浏览人员："] = "Parcourir personnel:";
catalog[" 所属权限组"] = " Niveau daccès";
catalog["当前不存在人员"] = "Aucune personne maintenant";
catalog["删除所属权限组"] = "Supprimer Niveau daccès";
catalog["请先选择要删除的权限组！"] = "Sil vous plaît sélectionner le niveau daccès que vous souhaitez supprimer.";
catalog["确认要删除人员所属权限组？"] = "Etes-vous sûr de vouloir supprimer le niveau daccès?";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_EmpLevel_Bylevel.html
catalog["数据处理进度"] = "Traitement de données Progrès";
catalog[" 的开门人员"] = " le personnel douverture";
catalog["当前不存在权限组"] = "Aucun niveau daccès maintenant";
catalog["从权限组中删除"] = "Supprimer du Niveau daccès";
catalog["权限组列表"]="Liste de Niveau daccès";
catalog["门列表"]="Liste des Portes"
catalog["人员列表"]="Liste de Personnel"
catalog["浏览 "]="Parcourir "
catalog["可以进出的门"]=" Ayant Niveau daccès"
catalog["当前不存在人员"]="Pas Personnel"
catalog["以人员查询"]="par Personnel"
catalog["以门查询"]="Par porte "
catalog["以权限组查询"]="par niveau daccès"
catalog["确认要从权限组中删除人员？"] = "?tes-vous sûr de vouloir supprimer la personne du niveau daccès?";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Monitor_All.html
catalog["远程开门"] = "Ouvrir à distance";
catalog["选择开门方式"] = "Choisissez le mode douverture de porte";
catalog["开门："] = "Ouvrez la porte pour ";
catalog[" 秒"] = " Seconde(s)";
catalog["常开"] = "Ouverture normale";
catalog["启用当天常开时间段"] = "Activer Passage intrajournalières mode fuseau horaire";
catalog["远程关门"] = "Fermeture à distance";
catalog["选择关门方式"] = "Choisissez le mode de fermeture des portes";
catalog["关门"] = "Fermer la porte";
catalog["禁用当天常开时间段"] = "Désactiver Passage intrajournalières mode fuseau horaire";
catalog["当前门处于常开状态，是否禁用当天常开时间段后关门？"] = "La porte actuelle est normal maintenant ouverte, si vous souhaitez désactiver Passage intrajournalières mode fuseau horaire et fermer la porte?";
catalog["当前已常开"] = "Actuellement normale ouverte";
catalog["发送请求失败！"] = "Echec de lenvoi de la demande!";
catalog["发送请求成功！"] = "Envoyer la demande avec succès !";
catalog["发送请求失败，请重试！"] = "Echec de lenvoi de la demande! Sil vous plaît essayer à nouveau!";
catalog["当前没有符合条件的门！"] = "Il ny a aucune porte qui répond à la condition.";
catalog["请输入有效的开门时长！必须为1-254间的整数！"] = "Sil vous plaît entrer un intervalle de porte-ouverte valide! Doit être un entier entre 1-254!";
catalog["禁用"] = "Désactivé";
catalog["离线"] = "Hors ligne";
catalog["报警"] = "Alarme";
catalog["门开超时"] = "Délai douverture";
catalog["关闭"] = "Fermé";
catalog["打开"] = "Ouvert";
catalog["无门磁"] = "Pas de capteur de porte";
catalog["当前设备状态不支持该操作！"] = "Etat actuel de lappareil ne supporte pas cette opération!";
catalog["该人员没有登记照片！"] = "Pas dimage.";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform_alarm.html
catalog["导出报表"] = "Exporter le rapport";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform_allevent.html
catalog["设置定时获取记录时间"] = "Réglez le temps pour lobtention de nouvelles entrées";
catalog["每天"] = "Obtenir de nouvelles entrées ";//特殊翻译请核对页面
catalog[" 点自动从设备获取新记录"] = " Heures chaque jour automatiquement.";
catalog["注：请确保服务器在设置的时间点处于开机状态。"] = "Remarque: Assurez-vous que le serveur est allumé pendant le temps que vous réglez.";
catalog["定时下载记录时间设置成功！该设置将在软件服务或者操作系统重启后生效！"] = "Réglage de réussir le temps! Les réglages ne prendront effet quaprès le redémarrage du service de logiciel ou le système dexploitation";
catalog["定时下载记录事件设置失败！请重试！"] = "Réglage de lheure échoué! Sil vous plaît essayer à nouveau!";
catalog["请输入有效的时间点(0-23)！"] = "Veuillez saisir une heure valide (0-23)!";
catalog["无"] = "Aucun";
catalog["注：1.请确保服务器在设置的时间点处于开机状态。<br/> 2.如需设置多个时间点，请以逗号分开。"] = "Remarque: 1. Veuillez veiller à ce que le serveur est activée dans le temps de réglage. <br/> 2. Pour définir plusieurs points de temps, séparés par des virgules.";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Acc_Reportform_emplevel.html
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Device_opform_OpChangeIPOfACPanel.html
catalog["请输入有效的IPv4地址！"] = "Veuillez saisir une adresse IPv4 valide.";
catalog["请输入有效的网关地址！"] = "Veuillez saisir une adresse de passerelle valide.";
catalog["请输入有效的子网掩码！"] = "Veuillez saisir un masque de sous-réseau valide.";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Device_opform_OpCtrlAuxOut.html
catalog["获取设备扩展参数失败，当前操作不可用！"] = "Impossible dobtenir les paramètres étendus pour appareil, lopération en cours ne sont pas disponibles!";
catalog["请选择要关闭的辅助输出点！"] = "Sil vous plaît vérifier le port auxiliaire vous voulez fermer.";
catalog["请选择辅助输出点！"] = "Sil vous plaît sélectionner le point de sortie auxiliaire.";
catalog["请输入正确的时间！"] = "Sil vous plaît entrez lheure correcte.";
//in file--D:\trunk\units\adms\mysite\iaccess\templates\Device_opform_OpSearchACPanel.html
catalog["退出"] = "Exit";
catalog["正在搜索中,请等待!"] = "Recherche. Sil vous plaît, attendez!";
catalog["当前共搜索到的门禁控制器总数为："] = "Le nombre total de panneaux de contrôle daccès est maintenant trouvé:";
catalog["自定义设备名称"] = "Personnalisez le nom du périphérique";
catalog["新增时删除设备中数据"] = "Effacer les données dans lappareil lors de lajout";
catalog["设备名称不能为空，请重新添加设备！"] = "Le nom de lappareil ne peut pas être vide. Sil vous plaît ajouter à nouveau un dispositif.";
catalog["的设备添加成功！"] = " Périphérique est ajouté avec succès!";
catalog["已添加设备数："] = "Nombre de dispositifs ajoutés:";
catalog["IP地址："] = "Adresse IP";
catalog[" 已存在！"] = "Existe déjà!";
catalog["序列号："] = "Numéro de série";
catalog["IP地址为："] = "Adresse IP:";
catalog[" 的设备添加失败！原因："] = " Echoué à être ajouté,raison :  ";
catalog[" 的设备添加异常！原因："] = " Périphérique est ajouté à titre exceptionnel, la raison: ";
catalog["的设备添加成功，但设备扩展参数获取失败！原因："] = " Périphérique est ajouté avec succès, mais son paramètre dextension ne parvient pas à être obtenu. raison:";
catalog["设备连接成功，但无数据返回，添加设备失败！"] = "Lappareil est connecté avec succès, mais il ny a pas de données retourné, indiquant que le périphérique ne parvient pas à être ajouté.";
catalog["设备连接失败(错误码："] = "Le dispositif ne parvient pas à être connecté (code derreur: ";
catalog[")，无法添加该设备！"] = "), so it cannot be added.";
catalog["设备连接失败(原因："] = "Le dispositif ne parvient pas à être connecté (Raison:";
catalog["修改设备IP地址"] = "Modifier Adresse IP du périphérique";
catalog["原IP地址"] = "Adresse IP dorigine";
catalog["新IP地址"] = "Nouvelle adresse IP";
catalog["网关地址"] = "Adresse de la passerelle";
catalog["子网掩码"] = "Masque de sous-réseau";
catalog["请输入设备通讯密码:"] = "Entrez un mot de passe de communication de lappareil:";
catalog["新的IP地址不能为空！"] = "La nouvelle adresse IP ne peut pas être vide.";
catalog["请输入一个有效的IPv4地址！"] = "Veuillez saisir une adresse IPv4 valide.";
catalog["请输入一个有效的网关地址！"] = "Veuillez saisir une adresse de passerelle valide.";
catalog["请输入一个有效的子网掩码！"] = "Veuillez saisir un masque de sous-réseau valide.";
catalog["该IP地址的设备已存在或该IP地址已被使用，不能添加！请重新输入！"] = "Il existe déjà un dispositif avec cette adresse IP ou ladresse IP a été utilisé, de ce fait il ne peut pas être ajouté. Sil vous plaît saisir un autre.";
catalog["操作失败！原因："] = "Lopération a échoué! raison:";
catalog["设备连接成功，但修改IP地址失败！"] = "Lappareil est connecté avec succès, mais ladresse IP ne parvient pas à être modifié.";
catalog["设备连接失败，故修改IP地址失败！"] = "Le dispositif ne parvient pas à être connecté, donc ladresse IP ne parvient pas à être modifié.";
catalog["没有搜索到门禁控制器！"] = "Aucun panneau de contrôle daccès trouvé.";
//in file--D:\trunk\units\adms\mysite\personnel\templates\Department_list.html
catalog["显示部门树"] = "Afficher département arbre";
catalog["隐藏部门树"] = "Cacher département arbre";
//in file--D:\trunk\units\adms\mysite\personnel\templates\EmpChange_edit.html
catalog["请选择一个调动栏位"] = "Sil vous plaît sélectionner une position de transfert.";
//in file--D:\trunk\units\adms\mysite\personnel\templates\EmpItemDefine_list.html
catalog["部门花名册"] = "Rouleau de departement";
catalog["学历构成分析表"] = "Analyse de la composition de léducation";
catalog["人员流动表"] = "Rapport de chiffre daffaires personnel";
catalog["人员卡片清单"] = "Liste des cartes du personnel";
catalog["请选择开始日期和结束日期"] = "Sil vous plaît sélectionner la date de début et date de fin.";
catalog["开始日期不能大于结束日期"] = "Date de début ne peut pas être postérieure à la date de fin.";
//in file--D:\trunk\units\adms\mysite\personnel\templates\Employee_edit.html
catalog["图片格式无效!"] = "Format dimage non valide";
catalog["人员编号必须为数字"] = "No personnel doit être numérique.";
catalog["请输入有效的E_mail!"]="Sil vous plaît entrer un E_mail valide!";
catalog["身份证号码不正确"] = "Mauvais numéro de carte didentité";
catalog["没有可选的门禁权限组！"] = "Aucun niveau daccès disponible.";
catalog["指纹模板错误，请立即联系开发人员！"] = "Erreur de modèle dempreintes digitales, sil vous plaît nous contacter dès que possible!";
catalog["指纹模板错误，请重新登记！"] = "Erreur de modèle dempreintes digitales, sil vous plaît inscrivez-vous à nouveau lempreinte digitale!";
catalog["请输入正确的电话号码"] = "Sil vous plaît entrez un numéro de téléphone valide!";
catalog["修改密码"] = "Modifier le mot de passe";
catalog["旧密码："] = "Ancien Mot de Passe:";
catalog["新密码："] = "New Password:";
catalog["确认密码："] = "Confirmer mot de passe:";
catalog["最大6位整数"] ="Max 6 chiffres entier";

//in file--D:\trunk\units\adms\mysite\personnel\templates\Employee_list.html
//in file--D:\trunk\units\adms\mysite\personnel\templates\Employee_opform_OpAddLevelToEmp.html
//in file--D:\trunk\units\adms\mysite\personnel\templates\IssueCard_opform_OpBatchIssueCard.html
catalog["每次发卡数量不能超过100"] = "Pas plus de 100 cartes peuvent être émises à un moment.";
catalog["起始编号长度不能超过"] = "La longueur du numéro de départ ne peut pas dépasser ";
catalog["位"] = " digits.";
catalog["结束编号长度不能超过"] = "La longueur du numéro de fin ne peut pas dépasser";
catalog["起始人员编号与结束人员编号的长度位数不同！"] = "Le n ° de début et de fin sont de longueur différente.";
//in file--D:\trunk\units\adms\mysite\personnel\templates\LeaveLog_list.html
//in file--D:\trunk\units\adms\mysite\worktable\templates\worktable_common_monitor.html
catalog["点击查看消息详情"] = "Cliquez pour voir le détail du message";
catalog["删除该消息"] = "Supprimer ce message";
catalog["公告详情"] = "Détails de notice";
//in file--D:\trunk\units\adms\mysite\worktable\templates\worktable_common_opt.html
catalog["保存成功!"] = "Sauvegarde Réussie";
catalog["人员选择:"] = "Sélectionnez une personne:";
//in file--D:\trunk\units\adms\mysite\worktable\templates\worktable_common_search.html
catalog["人员查询"] = "Requête du personnel";
catalog["人员编号"] = "N° Personnel.";
catalog["姓名"] = "Name";
catalog["身份证号查询"] = "Numéro didentification de la carte requête";
catalog["身份证号码"] = "Numéro de carte didentité";
catalog["考勤设备查询"] = "Participation requête de lappareil";
catalog["离职人员查询"] = "Requête du personnel de départ";
catalog["考勤原始数据查询"] = "participation originale requête de données";
catalog["员工调动查询"] = "Requête transfert de personnel ";
catalog["卡片查询"] = "Carte requête";
catalog["卡号"] = "Numéro de carte";
catalog["部门查询"] = "Département requête";
catalog["部门编号"] = "Numéro de département";
catalog["部门名称"] = "Nom de département";
catalog["补签卡查询"] = "Annexer journal requête";
catalog["服务器加载数据失败,请重试!"] = "Le serveur ne parvient pas à charger des données. Sil vous plaît essayer à nouveau.";
//in file--D:\trunk\units\adms\mysite\media\jslib\calculate.js
catalog["补签卡"] = "Annexer journal";
catalog["补请假"] = "Annexer congé";
catalog["新增排班"] = "Ajouter un planning";
catalog["临时排班"] = "Horaire temporaire";
catalog["结束日期不能大于今天"] = "Date de fin ne peut pas être plus tard aujourdhui.";
catalog["统计只能当月日期，或者天数不能超过开始日期的月份天数！ "] = "Statistiques ne concernent que les dates du mois, ou le nombre de jours concernés ne peuvent pas dépasser le nombre des jours contenus dans le mois de la date de début.";
catalog["统统计的时间可能会较长，请耐心等待"] = "Statistics of the time may be longer, please be patient";
catalog["请选择人员或部门"] = "Sil vous plaît sélectionner une personne ou un département.";
catalog["统计结果详情"] = "Résultat des statistiques";
catalog["每日考勤统计表"] = "Tableau statistique quotidien";
catalog["考勤明细表"] = "Détail de présence";
catalog["请假明细表"] = "Détail congé";
catalog["考勤统计汇总表"] = "statistique globale";
catalog["原始记录表"] = "AC tableau du journal";
catalog["补签卡表"] = "Annexer tableau du journal";
catalog["请假汇总表"] = "Laissez résumé";
catalog["请选择开始日期或结束日期!"] = "Sil vous plaît sélectionner la date de début ou de fin.";
catalog["开始日期不能大于结束日期!"] = "Date de début ne peut pas être postérieure à la date de fin.";
catalog["最多只能查询31天的数据!"] = "Tout au plus 31 jours de données peuvent être interrogées.";
catalog["请在查询结果中选择人员！"] = "Sil vous plaît une personne à partir du résultat de la requête.";
catalog["取消"] = "Annuler";
//in file--D:\trunk\units\adms\mysite\media\jslib\CDrag.js
catalog["展开"] = "Déplier";
catalog["收缩"] = "Plier";
catalog["自定义工作面板"] = "Personnaliser le panneau de travail";
catalog["锁定"] = "Bloquer";
catalog["解除"] = "Débloquer";
catalog["常用操作"] = "Opération commune";
catalog["常用查询"] = "Requête commune";
catalog["考勤快速上手"] = "Présence de démarrage rapide";
catalog["门禁快速上手"] = "Contrôle daccès de démarrage rapide";
catalog["系统提醒、公告"] = "Rappel du système et Notice";
catalog["人力构成分析"] = "Analyse du personnel de Composition";
catalog["最近门禁异常事件"] = "Exception récente de contrôle daccès";
catalog["本日出勤率"] = "Service tarif du jour";
catalog["加载中......"] = "Chargement...";
//in file--D:\trunk\units\adms\mysite\media\jslib\datalist.js
catalog["是否"] = "Yes/No";
catalog["选择所有 {0}(s)"] = "Tout sélectionner{0}(s)";
catalog["选择 {0}(s): "] = "Selectionner {0}(s):";
catalog["服务器处理数据失败，请重试！"] = "Le serveur ne parvient pas à traiter les données. Sil vous plaît essayer de nouveau!";
catalog["新建相关数据"] = "Créer données associées";
catalog["浏览相关数据"] = "Parcourir données associées";
catalog["添加"] = "Ajouter";
catalog["浏览"] = "Parcourir";
catalog["编辑"] = "Editer";
catalog["编辑这行数据"] = "Modifier cette ligne ";
catalog["升序"] = "Monter";
catalog["降序"] = "Descendre";
//in file--D:\trunk\units\adms\mysite\media\jslib\datalistadd.js
catalog["该模型不支持高级查询功能"] = "Ce modèle ne  supporte pas fonctions de requête avancées.";
catalog["高级查询"] = "Requête avancée";
catalog["导入"] = "Importer";
catalog["请选择一个上传的文件!"] = "Sil vous plaît sélectionner un fichier à télécharger.";
catalog["标题行号必须是数字!"] = "Un numéro de titre de ligne doit être un numérique.";
catalog["记录行号必须是数字!"] = "Un certain nombre dentrée de ligne doit être un numérique.";
catalog["请选择xls文件!"] = "Sil vous plaît sélectionner un fichier xls.";
catalog["请选择csv文件或者txt文件!"] = "Sil vous plaît sélectionner un fichier csv ou txt.";
catalog["文件标头"] = "Tête de fichier";
catalog["文件记录"] = "Enregistrement de fichier";
catalog["表字段"] = "Tableau déposé";
catalog["请先上传文件！"] = "Sil vous plaît télécharger un fichier en premier.";
catalog["导出"] = "Exporter";
catalog["页记录数只能为数字"] = "La quantité dentrées dans une page ne peut être un numérique.";
catalog["页码只能为数字"] = "Numéro de page ne peut être quun numérique.";
catalog["记录数只能为数字"] = "La quantité dentrées ne peut être un numérique.";
catalog["用户名"] = "Nom dutilisateur";
catalog["动作标志"] = "Action drapeau";
catalog["增加"] = "Ajouter";
catalog["修改"] = "Modifier";
catalog["删除"] = "Supprimer";
catalog["其他"] = "Autres";
//in file--D:\trunk\units\adms\mysite\media\jslib\electro_map.js
catalog["地图宽度到达上限(1120px)，不能再放大！"] = "Atteindre la limite supérieure de la largeur de la carte (1120px), ne peut pas agrandir!";
catalog["地图宽度到达下限(400px)，不能再缩小！"] = "Atteindre le minimum de la largeur de la carte (400px), ne peut pas réduite!";
catalog["地图高度到达下限(100px)，不能再缩小！"] = "Atteindre la limite minimale de la carte hauteur (100px), ne peut pas réduite!";
catalog["门图标的位置（Top或Left）到达下限，请稍作调整后再进行缩小操作！"] = "Lemplacement (haut ou à gauche) de licône de la porte a atteint au minimum, sil vous plaît faire quelques ajustements et puis continuer à affiner la carte!";

//in file--D:\trunk\units\adms\mysite\media\jslib\importAndExport.js
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.plus.js
catalog["信息提示"] = "Tips";
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.plus.js
catalog["日期"] = "date";
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.zcommon.js
catalog["标签页不能多于6个!"] = "Il ne peut y avoir plus de 6 onglets.";
catalog["按部门查找"] = "Recherche par département";
catalog["选择部门下所有人员"] = "Sélectionnez tout le personnel dans le département";
catalog["(该部门下面的人员已经全部选择!)"] = "(Tout le personnel de ce département ont été sélectionnés.)";
catalog["按人员编号/姓名查找"] = "Recherche par Personnel / Nom";
catalog["按照人员编号或姓名查找"] = "Recherche par Personnel / Nom";
catalog["查询"] = "Requête";
catalog["请选择部门"] = "Sélectionnez un département";
catalog["该部门下面的人员已经全部选择!"] = "Tout le personnel de ce département ont été sélectionnés.";
catalog["打开选人框"] = "Ouvrir la boîte de sélection";
catalog["收起"] = "Fermer";
catalog["已选择人员"] = "Personnel sélectionnés ";
catalog["清除"] = "Effacer";
catalog["编辑还未完成，已临时保存，是否取消临时保存?"] = "Le montage est pas encore terminée, et il est sauvegardé temporairement. Voulez-vous annuler la sauvegarde temporaire?";
catalog["恢复"] = "Restaurer";
catalog["会话已经过期或者权限不够,请重新登入!"] = "La session a expiré ou votre droit est limité. Sil vous plaît vous connecter à nouveau.";
//in file--D:\trunk\units\adms\mysite\media\jslib\jquery.zgrid.js
catalog["没有选择要操作的对象"] = "Aucun objet est sélectionné pour lopération";
catalog["进行该操作只能选择一个对象"] = "Un seul objet peut être sélectionné pour cette opération";
catalog["相关操作"] = "Opération associée";
catalog["共"] = "Total";
catalog["记录"] = "Entrée";
catalog["页"] = "Page";
catalog["首页"] = "Première";
catalog["前一页"] = "Précédente";
catalog["后一页"] = "Prochaine";
catalog["最后一页"] = "Dernière";
catalog["选择全部"] = "Tout";
//in file--D:\trunk\units\adms\mysite\media\jslib\widgets.js
catalog["January February March April May June July August September October November December"] = "January February March April May June July August September October November December";
catalog["S M T W T F S"] = "S M T W T F S";
//---------------------------------------------------------
catalog["记录条数不能超过10000"] = "Max 10000";
catalog["请输入大于0的数字"] = "Sil vous plaît entrer un nombre supérieur à 0";
catalog["当天存在员工排班时"] = "avait horaire en journée en cours";

catalog["暂无提醒及公告信息"] = "Aucun rappel et un avis";
catalog["关于"] = "? Propos  ";
catalog["版本号"] = "Numéro de version";
catalog["产品ID"] = "ID du produit";
catalog["本系统建议使用浏览器"] = "Les navigateurs que nous avons recommandées";
catalog["显示器分辨率"] = "Résolution de lécran";
catalog["及以上像素"] = "Pixels et au-dessus";
catalog["软件运行环境"] = "Lenvironnement dexécution de ce logiciel";
catalog["系统默认"] = "Par défaut";

catalog["photo"] = "Photo";
catalog["table"] = "Tableau";

catalog["此卡已添加！"] = "Cette carte a été ajoutée!";
catalog["卡号不正确！"] = "Le numéro de carte est erroné!";
catalog["请输入要添加的卡号！"] = "Saisissez le numéro de carte!";
catalog["请选择刷卡位置！"] = "Sil vous plaît sélectionner la position de la carte glissé!";
catalog["请选择人员！"] = "Selectionner une personne!";
catalog["table"] = "Tableau";
catalog["table"] = "Tableau";
catalog["首字符不能为空!"]="Le premier caractère ne peut pas être vide!";
catalog["密码长度必须大于4位!"]="Le mot de passe doit être supérieure à 4!";

catalog["当前列表中没有卡可供分配！"] = "Il ny a pas de carte peut être attribuée dans la liste actuelle!";
catalog["当前列表中没有人员需要分配！"] = "Il ny a pas besoin de personne pour attribuer carte dans la liste actuelle!";
catalog["没有已分配人员！"] = "Il ny avait aucune personne qui a été attribué!";
catalog["请先点击停止读取！"] = "Sil vous plaît arrêter de lire le numéro de carte dabord!";
catalog["请选择需要分配的人员！"] = "Sil vous plaît sélectionner la personne qui a besoin dassigner carte!";

catalog["请选择一个介于1到223之间的数值！"] = "Sil vous plaît spécifier une valeur comprise entre 1 et 223!";
catalog["备份路径不存在，是否自动创建？"] = "le chemin de sauvegarde nexiste pas,créer le automatiquement?";
catalog["处理中"] = "Traitement"
catalog["是"] = "Oui"
catalog["否"] = "Non"
//------------------------------------------------------------------------
//in file--D:\trunk\units\adms\mysite\media\jslib\worktable.js
catalog["已登记指纹"] = "Empreinte digitale enregistrée:"
//人员判断哪里 验证 输入不合法
catalog["不合法"] = "Illégale";

catalog["通讯密码"] = "Communication Mot de passe";

catalog["登记指纹功能只支持IE浏览器"] = "La fonction prend uniquement en charge le navigateur IE.";

catalog["请安装指纹仪驱动"] = "Sil vous plaît installer le pilote lecteur dempreintes digitales.";

catalog["解析xml文件出错"] = "Chargement xml Echoué!";

catalog["该通道已达最大访问量！"] = "Le numéro de canal du visiteur a atteint la valeur maximale!";

catalog["当前没有可用的角色,请先添加角色"] = "Pas de rôle disponibles au choix nowï¼Œ SVP créer un ou plusieurs rôles dabord!";

catalog["当前设备IP地址和服务器不在同一网段，请先将其调整到一个网段，再尝试添加！"] = "Le dispositif et le serveur sont dans le segment de réseau différent, sil vous plaît de les ajuster pour être le même segment de réseau et essayez à nouveau!";

catalog["数据库将备份到:"]="La base de données sera à Backupées:";

//
catalog["所选的部门总数不能大于2000"]="Département selectionnés ne peuvent pas dépasser 2000 au total";

catalog["操作成功！"] = "Lopération réussie!";
catalog["操作失败！"] = "Lopération a échoué!";
catalog["服务器处理数据失败，请重试！错误码："] = "Le serveur ne parvient pas à traiter les données. Sil vous plaît essayer à nouveau! Code derreur:";
catalog["重连间隔时间必须为整数！"] = "Lintervalle de reconnexion doit être un numérique!";
catalog["设置成功，重启服务后生效！"]="Régler avec succès, les paramètres prendront effet après le redémarrage du service de logiciel ou le système dexploitation";
catalog["设置成功！"]="Réglez avec succès!!";

//catalog["保存参数成功！"] = "Sauvegarde réussie!";
catalog["获取记录时间点不能为空！"] = "Le moment de lobtention de nouvelles entrées ne peut pas être vide!";

catalog["用户注册失败，请检查设备配置"] = "Impossible denregistrer un utilisateur, Sil vous plaît vérifier la configuration du périphérique";
catalog["目前该功能仅支持IE系列及IE内核的浏览器，请更换！"] = "Cette fonction ne peut que soutenir les navigateurs IE de la série. Sil vous plaît changer!";
catalog["请选择视频设备！"] = "Sil vous plaît choisir un dispositif!";
catalog["控件初始化失败，请确定视频设备类型是否选择正确或重装控件！"] = "Echec dinitialisation ocx, sil vous plaît assurez-vous que le type dappareil est correcte ou réinstaller ocx!";
catalog["预览失败"] = "Impossible de prévisualiser";
catalog["邮箱地址格式不正确"] = "Adresse mai invalide";
catalog["请输入邮箱地址"] = "Sil vous plaît entrez ladresse email";
catalog["邮件通知"] = "Notification par email";
catalog["报警监控"] = "La surveillance d alarme";
catalog["辅助输入"] = "Entrée auxiliaire";
catalog["辅助输出"] = "Sortie auxiliaire";
catalog["邮件通知"] = "Notification par email";
catalog["请输入邮箱地址"] = "Sil vous plaît entrez ladresse email";
catalog["请输入邮箱地址，多个地址用 ';' 隔开"] = "Sil vous plaît entrez ladresse E-mail, adresse avec plus;";
catalog["邮件发送成功!"] = "Mail envoyé avec succès!";
catalog["邮件发送失败!"] = "Envoi de mail Echoué!";
catalog["邮件发送失败,门禁参数配置中邮箱配置错误!"] = "Envoi de mail échoué, paramètres de contrôle daccès dans la configuration de la boîte aux lettres défaut de configuration!";
catalog["请选择报警设备!"] = "Sil vous plaît choisir le dispositif dalarme!";
catalog["门状态"] = "Etat de la porte";
catalog["门锁状态"] = "Etat porte";
catalog["报警类型"] = "Type dalarme";
catalog["门关报警"] = "Porte fermée et l alarme";
catalog["门开报警"] = "Ouvrir la porte et dalarme";
catalog["门开超时"] = "Délai douverture";
catalog["解锁"] = "Débloqué";
catalog["锁定"] = "Verrouillé";
catalog["没有报警"] = "Aucun";
catalog["防拆"] = "Sabotage";
catalog["胁迫密码开门"] = "Mot de passe contrainte douverture";
catalog["门被意外打开"] = "Ouvert avec force";
catalog["请先关闭门！"] = "Sil vous plaît fermer la porte dabord!";
catalog["胁迫开门"] = "Ouvrir Contrainte";
catalog["胁迫指纹开门"] = "Ouvrir Contrainte dempreintes digitales";
//in file--D:\trunk\units\adms\mysite\ Acc_Reportform.html
catalog["视频服务器登录失败，请确认后重试！原因："] = "Echec de connexion au serveur vidéo, sil vous plaît vérifier et essayer à nouveau! raison: ";
catalog["视频服务器登录失败，请确认后重试！错误码："] = "Echec de connexion au serveur vidéo, sil vous plaît verifier et essayer à nouveau! raison:  ";
catalog["视频回放失败，请确认后重试！原因："] = "Echec de la lecture de la vidéo, sil vous plaît vérifier et essayer à nouveau! raison: ";
catalog["视频回放失败，请确认后重试！错误码："] = "Echec de la lecture de la vidéo, sil vous plaît vérifier et essayer à nouveau! Code derreur: ";
catalog["视频服务器登录失败，请确认后重试！"] = "Echec de connexion au serveur vidéo, sil vous plaît vérifier et essayer à nouveau!"
//视频模块国际化-start
catalog["当前系统中没有添加视频服务器，请添加！"] = "Le système a aucun vidéo serveur.SVP ajouter un dabord!";
catalog["视频通道不能重复选择，请重新选择！"] = "Le canal vidéo ne peut pas être répété sélection, sil vous plaît Sélectionnez à nouveau!";
catalog["读头"] = "Lecteur";
catalog["名称"] = "Nom";
catalog["开门延时不能小于0，请输入正确的延时时长!"] = "L intervalle de temps de retard ne peut pas être inférieur à 0 s, sil vous plaît entrer le bon!";
catalog["视频时长不能小于0，请输入正确的视频时长!"] = "L intervalle daffichage de la vidéo ne peut pas être inférieur à 0 s, sil vous plaît entrer le bon!";
catalog["录像时长不能小于0，请输入正确的录像时长!"] = "L intervalle denregistrement vidéo ne peut pas être inférieur à 0 s, sil vous plaît entrer le bon!";
catalog["添加摄像机到当前地图"] = "Ajoutez des caméras sur la carte actuelle";
catalog["请选择要添加的摄像头！"] = "Sil vous plaît choisir les caméras que vous souhaitez ajouter!";
catalog["视频查询"] = "Recherche Vidéo";
catalog["视频联动"] = "Lien de la vidéo";
catalog["视频加载中，请稍侯......"] = "Chargement en cours, sil vous plaît patienter...";
catalog["该通道已达最大访问量或视频服务器未连接!"] = "Le canal a atteint son maximum de trafic de serveur vidéo est pas connecté!";
catalog["预览失败，请确认后重试！原因："] = "Aperçu échoue, assurez-vous et essayez à nouveau! raisons:";
catalog["预览失败，请确认后重试！错误码："] = "Aperçu échoue, assurez-vous et essayez à nouveau le code derreur!:";
catalog["无此权限！"] = "Aucune autorisation!";
catalog["没有录像文件！"] = "Aucun fichier vidéo!";
catalog["该通道已达最大访问量或视频服务器未连接！"] = "La chaîne a atteint son maximum de trafic ou un serveur _ nest pas branché";
catalog["从视频服务器导出失败！"] = "Exporter e-mail  à partir de serveur de la vidéo!";
catalog["从视频服务器导出成功！"] = "Réussite dexportation à partir du serveur de la vidéo!";
catalog["视频弹出窗口高度必须为整数！"] = "hauteur de la fenêtre Vidéo pop-up doit être un entier!";
catalog["请选择需要设置的对象!"] = "Sil vous plaît sélectionner lobjet que vous avez besoin de mettre en place!";
catalog["请启用当前视频设备下被禁用的视频通道！"] = "Sil vous plaît activer canal vidéo de léquipement vidéo actuel!";
//海康dvr last_error
catalog["HIKVISION_ERROR_1"] = "Utilisateur ou mot de passe erroné.";
catalog["HIKVISION_ERROR_4"] = "Mauvaise chaîne No.";
catalog["HIKVISION_ERROR_5"] = "Dépasser le nombre maximum de client pour se connecter au DVR.";
catalog["HIKVISION_ERROR_7"] = "Impossible de se connecter au DVR.";
catalog["HIKVISION_ERROR_8"] = "Echec de lenvoi des données à DVR.";
catalog["HIKVISION_ERROR_10"] = "Délai lors de lobtention des données de DVR.";
catalog["HIKVISION_ERROR_17"] = "Paramètre erronée.";
catalog["HIKVISION_ERROR_19"] = "Pas de disque dur.";
catalog["HIKVISION_ERROR_20"] = "Erreur de disque dur.";
catalog["HIKVISION_ERROR_21"] = "Disque dur du serveur est plein.";
catalog["HIKVISION_ERROR_22"] = "Erreur de serveur de disque dur.";
catalog["HIKVISION_ERROR_24"] = "Serveur occupé.";
catalog["HIKVISION_ERROR_28"] = "Manque de ressources DVR.";
catalog["HIKVISION_ERROR_29"] = "DVR Opération Echouée.";
catalog["HIKVISION_ERROR_33"] = "Server na pas le fichier spécifié pendant la lecture.";
catalog["HIKVISION_ERROR_36"] = "The last operation is not yet complete.";
catalog["HIKVISION_ERROR_38"] = "Erreur de lecture.";
catalog["HIKVISION_ERROR_46"] = "Le nombre maximal.";
catalog["HIKVISION_ERROR_47"] = "Utilisateur nexiste pas.";
catalog["HIKVISION_ERROR_52"] = "Le plus grand nombre dutilisateurs.";
catalog["HIKVISION_ERROR_74"] = "ID utilisateur dans lannulation de subir une opération.";
catalog["HIKVISION_ERROR_90"] = "Dispositif sauvegardé.";
catalog["许可信息"] = "Informations sur la licence";
catalog["请切换为英文输入法状态！"] = "Sil vous plaît passer à une entrée anglaise état de la méthode!";
catalog["许可信息"] = "Informations sur la licence";
catalog["请选择每个扩展板的继电器数量！"] = "Sil vous plaît sélectionner le nombre de relais pour chaque carte étendue!";
//登录页面验证
catalog["比对验证中，请稍等!"] = "Vérification, sil vous plaît patienter!";
catalog["验证失败，请重试!"] = "Echoué! Sil vous plaît essayer à nouveau!";
catalog["10.0指纹算法许可失败!"] = "Lalgorithme 10,0 licence dempreintes digitales Vérification Echouée!";
catalog["验证通过，登录系统!"] = "Vérifié, lexploitation  dans le système!";
catalog["获取指纹失败，请重试!"] = "Impossible dobtenir des empreintes digitales, sil vous plaît essayer à nouveau!";
catalog["登记指纹功能只支持IE浏览器"] = "La fonction ne supporte que le navigateur IE.";
catalog["请安装指纹仪驱动"] = "Sil vous plaît installer le pilote Lecteur dempreintes digitales";
//访客
catalog["进入地点"] = "Lieu de lentrée";
catalog["离开地点"] = "Lieu de sortie";
catalog["被访人姓名"] = "Prénom de Personnel ";
catalog["被访人姓氏"] = "Nom de personnel";
catalog["是否重新打印访客单？"] = "Réimpression de visiteurs uniques?";
catalog["没有注册读写器控件，是否下载控件？"] = "Non enregistré le contrôle du lecteur si vous souhaitez télécharger les contrôles?";
catalog["没有注册扫描仪控件，是否下载控件？"] = "Ne pas avoir un contrôle du scanner enregistré, si vous souhaitez télécharger les contrôles?";
catalog["暂时不支持该证件类型！"] = "Temporairement ne supporte pas le type de document!";
catalog["请选择正确的证件类型或调整证件的位置！"] = "Sil vous plaît sélectionner les documents dajustement de type de document ou de localisation correcte!";
catalog["加载核心失败！"] = "Echec de caragement de base!";
catalog["初始化失败！"] = "Linitialisation a échoué!";
catalog["请放好身份证！"] = "Sil vous plaît ranger votre ID!";
catalog["没有检测到身份证阅读器！"] = "Lecteur de carte ID ne soit pas détecté!";
catalog["目前该功能仅支持二代身份证！"] = "Cette fonctionnalité supporte que la carte ID de deuxième génération!";
catalog["没有可选的权限组！"] = "Pas de niveau disponible.";
catalog["卡号已存在，如果确认将重新发卡，请先清除该卡原持卡人"] = "Le numéro de carte existe déjà. Si vous voulez ré-émission une carte, retirez dabord le titulaire original de la carte ";
catalog["临时"] = "Temporairment";
catalog["get_visit_state"] = " tat visiteur";
//init_base_frame.js
catalog["正式版许可"] = "La version officielle de licence";
catalog["试用版许可"] = "La licence dévaluation";
catalog["断开"] = "Déconnecté";
catalog["短路"] = "Court-circuit";
//Employee_edit.html
catalog["没有可选的梯控权限组！"] = "Aucun niveau dascenseur disponible.";

//Dev_RTMonitor.html
catalog["请先停止监控再导出！"] = "Sil vous plaît arrêter la surveillance avant lexportation!";
catalog["服务未启动"] = "Service ne fonctionne pas";
catalog["门禁服务未启动，请先点击左方启动服务按钮"]= "Service daccès na pas démarré, sil vous plaît cliquer sur le bouton «Démarrer le service« gauche";
catalog["门禁服务开启成功！"] = "Démarrez le service daccès avec succès!";
catalog["邮箱测试发送成功！"] = "Essai denvoi email avec succès!";
catalog["接收者邮箱地址格式不正确！"] = "Adresse de boîte aux lettres non valide pour recevoir!";
catalog["请选择开始时间"] = "Sil vous plaît Sélectionnez lheure de début";
catalog["请选择结束时间"] = "Sil vous plaît Sélectionnez lheure de fin";
catalog["只能查询3个月内的数据"] = "Seules les données de la requête dans les trois mois";
catalog["只能查询2个月内的数据"] = "Seules les données de la requête dans les deux mois";
catalog["只能查询1个月内的数据"] = "Seules les données de la requête dans un mois";

//in file--D:\trunk\units\adms\mysite\ Acc_Option.html
catalog["发件人邮箱地址格式不正确"] = "Adresse de la boîtes aux lettres est mal formaté";
catalog["收件人邮箱地址格式不正确"] = "Adresse du destinataire est mal formaté";
catalog["请输入邮件服务器(SMTP)地址"] = "Sil vous plaît entrez serveur de messagerie (SMTP)";
catalog["服务器端口只能为数字"] = "Port du serveur ne peut être un numérique";
catalog["服务器端口不能为0"] = "Server port can not be 0";
catalog["夏令时时间只能为数字！"] = "Le temps DST ne peut être un numérique!";
catalog["只支持导入Excel文件！"] = "Support que le fichier Excel!";
catalog["请选择要测试的门！"] = "Sil vous plaît choisir la porte d essai!";





