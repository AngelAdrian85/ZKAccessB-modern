// -*- coding: utf-8 -*-
___f=function(){
jQuery.validator.messages.required="Requerido"
jQuery.validator.messages.email="No es una dirección de correo electrónico"
jQuery.validator.messages.date="Ingrese una fecha válida: yyyy/mm/dd."
jQuery.validator.messages.dateISO="Ingrese una fecha (ISO) válida: yyyy-mm-dd."
jQuery.validator.messages.wZBaseDateField="Ingrese una fecha válida: yyyy-mm-dd."
jQuery.validator.messages.wZBaseDateTimeField="Ingrese una fecha válida: yyyy-mm-dd hh:mm:ss."
jQuery.validator.messages.wZBaseTimeField="Ingrese una hora válida: hh:mm:ss."
jQuery.validator.messages.wZBaseIntegerField="Ingrese un número entero."
jQuery.validator.messages.number="Ingrese un valor válido."
jQuery.validator.messages.digits="Solo se permiten valores numéricos"
jQuery.validator.messages.equalTo="Diferentes"
jQuery.validator.messages.minlength=$.validator.format("al menos {0} caracteres (s)")
jQuery.validator.messages.maxlength=$.validator.format("en la mayoría de {0} caracteres (s)")
jQuery.validator.messages.rangelength=$.validator.format("entre {0} y {1} caracteres")
jQuery.validator.messages.range=$.validator.format("Entre {0} y {1} CARACTERES")
jQuery.validator.messages.max=$.validator.format("Entre {0} y {1} CARACTERES")
jQuery.validator.messages.min=$.validator.format("Ingrese un valor no menor que {0}.")
jQuery.validator.messages.xPIN="solo se permiten caracteres alfanuméricos"
jQuery.validator.messages.xNum="Solo se permiten números enteros"
jQuery.validator.messages.xMobile="Número de teléfono móvil incorrecto"
jQuery.validator.messages.xTele="Número de teléfono incorrecto"
jQuery.validator.messages.xSQL="\" ó \'. no permitido"
}

___f();

if(typeof(catalog)=="undefined") {catalog={}}

catalog["请选择一个字段"] = "Seleccione un campo.";
catalog["输入的值错误"] = "Los datos ingresados son incorrectos.";

catalog["确定注销系统?"] = "¿Está seguro de salir?";
catalog["通讯失败"] = "Comunicación fallida";
catalog["确定"] = "Aceptar";

catalog["日志"] = "Eventos";


catalog["请选择一条历史备份记录!"] = "Seleccione un archivo de respaldo.";
catalog["还原成功!"] = "Restauración realizada con éxito";

catalog["间隔时间不能超过一年"] = "El intervalo no puede exceder un año.";
catalog["间隔时间不能为空"] = "Interval cannot  be empty.";
catalog["间隔时间不能为零"] = "Interval cannot  be zero.";
catalog["间隔时间不能小于24小时"] = "El intervalo no puede ser menor de 24 horas.";
catalog["在当前时间的一个小时内只能备份一次"] = "Debe esperar una hora para poder realizar otro archivo de respaldo";
catalog["请先在服务控制台中设置数据库备份路径"] = "Establezca la ruta para guardar el archivo de respaldo desde la consola de servicio";

catalog["全部"] = "Todos";

catalog["数据格式必须是json格式!"] = "Los datos deben estar en formato JSON.";

catalog["请选择人员!"] = "Seleccione una persona!";
catalog["考勤"] = "Asistencia";

catalog["设备名称不能为空"] = "Ingrese el nombre de dispositivo.";
catalog["设备序列号不能为空"] = "Ingrese el número de serie del dispositivo";
catalog["通讯密码必须为数字"] = "La contraseña de comunicación debe ser un valor numérico.";
catalog["请输入一个有效的IPv4地址"] = "Ingrese una dirección IPv4 válida.";
catalog["请输入一个有效的IP端口号"] = "Ingrese un número de puerto válido";
catalog["请输入一个RS485地址"] = "Ingrese una dirección de RS485.";
catalog["RS485地址必须为1到63之间的数字"] = "La dirección RS485 debe ser un valor entre 1 y 63.";
catalog["请选择串口号"] = "Seleccione un número de puerto serial.";
catalog["请选择波特率"] = "Seleccione la velocidad de transmisión.";
catalog["请选择设备所属区域"] = "Seleccione un área para el dispositivo.";
catalog["串口：COM"] = "Puerto serial COM";
catalog[" 的RS485地址："] = "Dirección RS485";
catalog[" 已被占用！"] = "Ya existe!";
catalog["后台通讯忙，请稍后重试！"] = "Comunicación ocupada. Intente más tarde.";
catalog["提示：设备连接成功，但获取设备扩展参数失败"] = "El dispositivo se conectó correctamente pero no se logró obtener los parámetros del dispositivo";
catalog["，继续添加？"] = " , ¿agregar de todas formas?";
catalog["提示：设备连接成功，但控制器类型与实际不符，将修改为"] = "El dispositivo se conectó correctamente pero el tipo de panel de acceso es diferente al ingresado. Será modificado a ";
catalog["门控制器，继续添加？"] = "puerta (s) del panel de control. Desea agregarlo?";
catalog["提示：设备连接成功，确定后将添加设备！"] = "El dispositivo está conectado y los datos son correctos. El dispositivo será agregado después de confirmar.";
catalog["提示：设备连接失败（错误码："] = "Conexión fallida (código de error:";
catalog["），确定添加该设备？"] = "¿Está seguro de agregar el dispositivo?";
catalog["提示：设备连接失败（原因："] = "Conexión fallida. (causa:";
catalog["编辑设备信息("] = "Editar la información del dispositivo (";
catalog["对不起，您没有访问该页面的权限，不能浏览更多信息！"] = "No tiene privilegio";
catalog["对不起,您没有访问该页面的权限,不能浏览更多信息！"] = "No tiene privilegio";
catalog["员工排班表"] = "Tabla de Horarios de Personal";
catalog["临时排班表"] = "Tabla de horario temporal";
catalog["排班时间段详细明细"] = "Calendario de turnos";
catalog["排班时间段详细明细(仅显示三个月)"] = "turnos de detalles el calendario (sólo tres meses)";
catalog["排班时间段详细明细(仅显示到年底)"] = "turnos de detalles el calendario (sólo el final del ejercicio";

catalog["请选择时段"] = "Seleccione turno";
catalog["选择日期"] = "Seleccione la fecha";
catalog["第"] = "No";
catalog["天"] = "Día";
catalog["周的周期不能大于52周"] = "Un período semanal no puede superar las 52 semanas.";
catalog["月的周期不能大于12个月"] = "Un periodo mensual no puede exceder de 12 meses.";
catalog["第"]="No.   ";  
catalog["天"] = "día";

catalog["时间段明细"] = "Detalles del turno";
catalog["确定删除该时段吗？"] = "¿Está seguro de eliminar el turno?";
catalog["操作失败 {0} : {1}"] = "Operación fallida {0}: {1}";

catalog["已选择"] = "seleccionados";

catalog["日期格式输入错误"] = "Formato de fecha incorrecta";
catalog["日期格式不正确！"] = "Formato de fecha incorrecta";  
catalog["夏令时名称不能为空！"] = "Debe ingresar un nombre para el horario de verano";  
catalog["起始时间不能和结束时间相等！"] = "La Hora inicial no puede ser igual a la hora final";

catalog["请选择一个班次"] = "Seleccione un turno";
catalog["结束日期不能小于开始日期!"] = "La fecha final no puede ser anterior a la fecha inicial";
catalog["请输入开始日期和结束日期! "] = "Ingrese la fecha inicial y fecha final.";
catalog["只能设置一个班次! "] = "Sólo puede establecer un turno.";

catalog["当前选择设备的扩展参数获取失败，无法对该设备进行反潜设置！"] = "No se pudo obtener los parámetros del dispositivo. No se puede configurar la función Anti-passback.";
catalog["读取到错误的设备信息，请重试！"] = "La información del dispositivo es incorrecto. Intente de nuevo.";
catalog["或"] = " o";
catalog["反潜"] = " Anti-passback";
catalog["读头间反潜"] = "Anti-passback entre los lectores";
catalog["反潜"] = " Anti-passback";



catalog["当前门:"] = "Puerta actual:";

catalog["删除开门人员"] = "Eliminar usuarios";
catalog["请先选择要删除的人员！"] = "Seleccione el usuario que desea eliminar.";
catalog["确认要从首卡常开设置信息中删除开门人员？"] = "¿Está seguro de eliminar el usuario?";

catalog["当前选择设备的扩展参数获取失败，无法对该设备进行互锁设置！"] = "No se pudo obtener los parámetros del dispositivo. No se puede configurar la función de esclusamiento.";
catalog["门:"] = "Puerta: ";
catalog["与"] = " y ";
catalog["互锁"] = " Esclusadas";


catalog["数据下载进度"] = "Progreso de la descarga";
catalog["设备名称"] = "Nombre del dispositivo";
catalog["总进度"] = "Progreso total";


catalog["当前选择设备的扩展参数获取失败，无法对该设备进行联动设置！"] = "No se pudo obtener los parámetros del dispositivo. No se pudo configurar el vínculo.";
catalog["请输入联动设置名称！"] = "Ingrese el nombre del vínculo.";


catalog["请选择地图！"] = "Seleccione el mapa.";
catalog["图片格式无效！"] = "Formato de imagen no válido.";

catalog["浏览多卡开门人员组："] = "Examinando grupo de verificación multi-ususario: ";
catalog[" 的人员"] = " - Miembros del grupo:";
catalog["当前不存在多卡开门人员组"] = "No existen grupos de verificación multi-usuario";
catalog["删除人员"] = "Eliminar usuario del grupo";
catalog["确认要从多卡开门人员组中删除人员？"] = "¿Está seguro de eliminar al usuario del grupo?";

catalog["请至少在一个组内填入开门人数！"] = "Ingrese un número de personal en al menos un grupo.";
catalog["至少两人同时开门！"] = "Debe seleccionar al menos dos personas para la verificación multi-usuario.";
catalog["最多五人同时开门！"] = "Se pueden establecer máximo cinco personas personas para la verificación multi-usuario.";
catalog["人"] = "Persona";
catalog["您还没有设置多卡开门人员组！请先添加！"] = "No se han establecido grupos de verificación multi-usuario.";

catalog["请在文本框内输入有效的时间！"] = "Ingrese un horario válido.";

catalog["对不起,您没有韦根卡格式设置的权限,不能进行当前操作！"] = "No tiene privilegio para modificar el formato Wiegand. No se puede realizar la operación.";



catalog["添加门到当前地图"] = "Agregar puertas en el mapa actual";
catalog["请选择要添加的门！"] = "Seleccione las puertas que desea agregar";
catalog["确定要删除当前电子地图："] = "¿Seguro de eliminar el mapa actual:";

catalog["添加辅助点到当前地图"] = "Agregar salida auxiliar en el mapa actual.";
catalog["请选择要添加的辅助点！"] = "Seleccione la salida auxiliar que desea agregar";

catalog["浏览人员："] = "Examinar personal:";
catalog[" 所属权限组"] = "Nivel de acceso";
catalog["当前不存在人员"] = "Sin personas";
catalog["删除所属权限组"] = "Eliminar del nivel de acceso";
catalog["请先选择要删除的权限组！"] = "Seleccione el nivel de acceso que desea eliminar.";
catalog["确认要删除人员所属权限组？"] = "¿Está seguro de eliminar al usuario del nivel de acceso?";

catalog["数据处理进度"] = "Procesando datos";
catalog[" 的开门人员"] = " - Usuarios asignados:";
catalog["当前不存在权限组"] = "Sin nivel de acceso";
catalog["从权限组中删除"] = "Eliminar del nivel de acceso";
catalog["确认要从权限组中删除人员？"] = "¿Está seguro de eliminar a la persona del nivel de acceso?";

catalog["远程开门"] = "Abrir remotamente";
catalog["选择开门方式"] = "Seleccione la opción";
catalog["开门："] = "Abrir la puerta ";
catalog[" 秒"] = " Segundos";
catalog["常开"] = "Normalmente abierto";
catalog["启用当天常开时间段"] = "Activar horario de apertura programado";
catalog["远程关门"] = "Cerrar remotamente";
catalog["选择关门方式"] = "Seleccione el modo de cierre";
catalog["关门"] = "Cerrar la puerta";
catalog["禁用当天常开时间段"] = "Desactivar horario de apertura programado";
catalog["当前没有符合条件的门！"] = "El estado actual del dispositivo no permite realizar la operación.";
catalog["请输入有效的开门时长！必须为1-254间的整数！"] = "El tiempo de apertura debe ser de 1 a 254 segundos.";
catalog["离线"] = "En línea";
catalog["报警"] = "Alarma";
catalog["门开超时"] = "Puerta mantenida abierta";
catalog["关闭"] = "Cerrada";
catalog["打开"] = "Abierta";
catalog["无门磁"] = "Sin sensor de puerta";


catalog["导出报表"] = "Exportar reporte";



catalog["请输入有效的IPv4地址！"] = "Ingrese una dirección IPv4 válida.";
catalog["请输入有效的网关地址！"] = "Ingrese una puerta de enlace válida.";
catalog["请输入有效的子网掩码！"] = "Ingrese una máscara de subred válida.";

catalog["获取设备扩展参数失败，当前操作不可用！"] = "No se pudo obtener los parámetros del dispositivo, la operación actual no está disponible!";
catalog["请选择要关闭的辅助输出点！"] = "Seleccione la salida auxiliar que desea cerrar.";
catalog["请选择辅助输出点！"] = "Seleccione el punto de salida auxiliar.";
catalog["请输入正确的时间！"] = "Ingrese la hora correcta.";
catalog["退出"] = "Salir";
catalog["正在搜索中,请等待!"] = "Buscando...";
catalog["当前共搜索到的门禁控制器总数为："] = "Dispositivos encontrados: ";
catalog["自定义设备名称"] = "Ingresar datos del dispositivo";
catalog["设备名称不能为空，请重新添加设备！"] = "Debe ingresar un nombre para el dispositivo. Agregue un dispositivo nuevo.";
catalog["的设备添加成功！"] = "Agregado correctamente!";
catalog["已添加设备数："] = "Dispositivos agregados: ";
catalog["IP地址："] = "Dirección IP";
catalog[" 已存在！"] = "El dispositivo ya existe!";
catalog["序列号："] = "Número de serie";
catalog["IP地址为："] = "Dirección IP:";
catalog[" 的设备添加失败！原因："] = "Falla al agregar. Causa: ";
catalog[" 的设备添加异常！原因："] = "Se agregó un dispositivo anormalmente. Causa: ";
catalog["的设备添加成功，但设备扩展参数获取失败！原因："] = "Se agregó el dispositivo correctamente pero no se pudieron obtener los parámetros. Causa: ";
catalog["设备连接成功，但无数据返回，添加设备失败！"] = "El dispositivo se conectó pero no retornó datos. El dispositivo no se pudo agregar.";
catalog["设备连接失败(错误码："] = "Conexión fallida (código de error:";
catalog[")，无法添加该设备！"] = "). El dispositivo no fue agregado.";
catalog["设备连接失败(原因："] = "Conexión fallida (causa:";
catalog["修改设备IP地址"] = "Cambiar la dirección IP del dispositivo";
catalog["原IP地址"] = "Dirección IP Actual";
catalog["新IP地址"] = "Nueva dirección IP";
catalog["网关地址"] = "Puerta de enlace";
catalog["子网掩码"] = "Máscara de subred";
catalog["请输入设备通讯密码:"] = "Ingrese la contraseña de comunicación del dispositivo:";
catalog["新的IP地址不能为空！"] = "Debe ingresar la nueva dirección IP.";
catalog["请输入一个有效的IPv4地址！"] = "Ingrese una dirección IPv4 válida.";
catalog["请输入一个有效的网关地址！"] = "Ingrese una puerta de enlace válida.";
catalog["请输入一个有效的子网掩码！"] = "Ingrese una máscara de subred válida.";
catalog["该IP地址的设备已存在或该IP地址已被使用，不能添加！请重新输入！"] = "Ya existe un dispositivo agregado con esa dirección IP o ya está siendo utilizada. Ingrese otra IP.";
catalog["设备连接成功，但修改IP地址失败！"] = "El dispositivo se conectó correctamente pero la dirección IP no pudo ser modificada.";
catalog["设备连接失败，故修改IP地址失败！"] = "Conexión fallida. No se pudo modificar la IP.";
catalog["没有搜索到门禁控制器！"] = "No se encontró ningún dispositivo.";

catalog["显示部门树"] = "Desplegar los departamentos";
catalog["隐藏部门树"] = "Ocultar los departamentos";

catalog["请选择一个调动栏位"] = "Seleccione una posición de transferencia.";

catalog["部门花名册"] = "Lista de departamentos";
catalog["学历构成分析表"] = "Nivel de educación";
catalog["人员流动表"] = "Lista de movimientos de personal";
catalog["人员卡片清单"] = "Lista de tarjetas de personal";
catalog["请选择开始日期和结束日期"] = "Seleccione la fecha inicial y final.";
catalog["开始日期不能大于结束日期"] = "La fecha inicial no puede ser posterior a la fecha final.";

catalog["图片格式无效!"] = "El formato de imagen no es válido";
catalog["人员编号必须为数字"] = "El ID debe ser numérico.";
catalog["请输入有效的E_mail!"]="Ingrese un correo válido.";  
catalog["身份证号码不正确"] = "Número de ID incorrecto";
catalog["没有可选的门禁权限组！"] = "Ningún nivel de acceso disponible.";
catalog["指纹模板错误，请立即联系开发人员！"] = "Error de plantilla de huella digital";

catalog["修改密码"] = "Modificar contraseña";
catalog["旧密码："] = "Contraseña anterior:";
catalog["新密码："] = "Contraseña nueva:";
catalog["确认密码："] = "Confirmar contraseña:";
catalog["最大6位整数"] =" Máximo 6 dígitos";  




catalog["每次发卡数量不能超过100"] = "No se pueden registrar más de 100 tarjetas a la vez.";
catalog["起始编号长度不能超过"] = "El número inicial no debe ser mayor de";
catalog["位"] = " dígitos.";
catalog["结束编号长度不能超过"] = "El número final no debe ser mayor de";
catalog["起始人员编号与结束人员编号的长度位数不同！"] = "El número inicial y final son de longitud diferente.";


catalog["点击查看消息详情"] = "Haga clic para ver el mensaje";
catalog["删除该消息"] = "Eliminar este mensaje";
catalog["公告详情"] = "Detalles";

catalog["保存成功!"] = "Guardado exitoso!";
catalog["人员选择:"] = "Seleccione un usuario:";

catalog["人员查询"] = "Búsqueda de usuarios";
catalog["人员编号"] = "ID del usuario";
catalog["姓名"] = "Nombre";
catalog["身份证号查询"] = "Búsqueda de ID";
catalog["身份证号码"] = "Número de ID";
catalog["考勤设备查询"] = "Dispositivo de asistencia";
catalog["离职人员查询"] = "Búsqueda por salidas";
catalog["考勤原始数据查询"] = "datos de la atención inicial de consulta";
catalog["员工调动查询"] = "personal de la transferencia de consulta";
catalog["卡片查询"] = "Búsqueda de tarjeta";
catalog["部门查询"] = "Búsquede de departamento";
catalog["部门编号"] = "Número del departamento";
catalog["部门名称"] = "Nombre del departamento";
catalog["补签卡查询"] = "Búsqueda de eventos";
catalog["服务器加载数据失败,请重试!"] = "Operación fallida. Intente de nuevo.";

catalog["补签卡"] = "Anexar entrada";
catalog["补请假"] = "Anexar salida";
catalog["新增排班"] = "Agregar calendario";
catalog["临时排班"] = "programación temporal";
catalog["结束日期不能大于今天"] = "Fecha de finalización no puede ser posterior al día de hoy.";
catalog["统计只能当月日期，或者天数不能超过开始日期的月份天数！ "] = "Estadísticas involucran sólo las fechas de cada mes, o el número de días en cuestión no puede exceder el número de los días que figura en el mes de la fecha de inicio.";
catalog["请选择人员或部门"] = "Por favor, seleccione a una persona o departamento.";
catalog["统计结果详情"] = "resultado de la estadística";
catalog["每日考勤统计表"] = "cuadro estadístico de todos los días";
catalog["考勤明细表"] = "asistencia detalle";
catalog["请假明细表"] = "Deja los detalles";
catalog["考勤统计汇总表"] = "estadística de resumen";
catalog["原始记录表"] = "CA tabla de registro";
catalog["补签卡表"] = "anexar registro de la tabla";
catalog["请假汇总表"] = "Deja resumen";
catalog["请选择开始日期或结束日期!"] = "Por favor seleccione la fecha de inicio o fecha de finalización.";
catalog["开始日期不能大于结束日期!"] = "Fecha de inicio no puede ser posterior a la fecha de finalización.";
catalog["最多只能查询31天的数据!"] = "En la mayoría de los 31 días de los datos se pueden consultar.";
catalog["请在查询结果中选择人员！"] = "Por favor, una persona del resultado de la consulta.";
catalog["取消"] = "Cancelar";

catalog["展开"] = "Desplegar";
catalog["收缩"] = "Ocultar";
catalog["自定义工作面板"] = "Personalizar Paneles";
catalog["锁定"] = "Puerta";
catalog["解除"] = "Desbloquear";
catalog["常用操作"] = "Panel de Acceso Rápido";
catalog["常用查询"] = "Búsquedas recurrentes";
catalog["考勤快速上手"] = "Inicio rápido";
catalog["门禁快速上手"] = "Panel de Inicio Rápido";
catalog["系统提醒、公告"] = "Sistema de recordatorio y aviso";
catalog["人力构成分析"] = "Personal de análisis de la composición";
catalog["最近门禁异常事件"] = "Acceso recientes excepciones de control";
catalog["本日出勤率"] = "Promedio de Asistencia de la Jornada";
catalog["加载中......"] = "cargando ...";

catalog["是否"] = "Sí / No";
catalog["选择所有 {0}(s)"] = "Seleccionar todos los {0} (s)";
catalog["选择 {0}(s): "] = "Seleccionó {0}: ";
catalog["服务器处理数据失败，请重试！"] = "El servidor no puede procesar los datos. Intente de nuevo.";
catalog["新建相关数据"] = "Crear los datos relacionados";
catalog["浏览相关数据"] = "Examinar datos relacionados";
catalog["添加"] = "Agregar";
catalog["浏览"] = "Examinar";
catalog["编辑"] = "Editar";
catalog["编辑这行数据"] = "Edición de la fila";
catalog["升序"] = "Ascender";
catalog["降序"] = "Descender";

catalog["该模型不支持高级查询功能"] = "Este modelo no soporta las funciones de búsqueda avanzada";
catalog["高级查询"] = "Búsqueda Avanzada";
catalog["导入"] = "Importar";
catalog["请选择一个上传的文件!"] = "Seleccione un archivo.";
catalog["标题行号必须是数字!"] = "El número de fila título debe ser un valor numérico.";
catalog["记录行号必须是数字!"] = "El número de filas debe ser numérico.";
catalog["请选择xls文件!"] = "Seleccione un archivo xls.";
catalog["请选择csv文件或者txt文件!"] = "Seleccione un archivo csv o txt.";
catalog["文件标头"] = "Título del archivo";
catalog["文件记录"] = "Archivo de registro";
catalog["表字段"] = "Tabla de campos";
catalog["请先上传文件！"] = "Cargue un archivo.";
catalog["导出"] = "Exportar reporte";
catalog["页记录数只能为数字"] = "La cantidad de entradas en una página sólo puede ser un valor numérico.";
catalog["页码只能为数字"] = "El número de página sólo puede ser un valor numérico.";
catalog["记录数只能为数字"] = "La cantidad de entradas sólo puede ser un valor numérico.";
catalog["用户名"] = "Usuario";
catalog["动作标志"] = "Tipo de Evento";
catalog["增加"] = "Agregar";
catalog["修改"] = "Modificar";
catalog["删除"] = "Eliminar";
catalog["其他"] = "Otros";

catalog["门图标的位置（Top或Left）到达下限，请稍作调整后再进行缩小操作！"] = "La posición del ícono de la puerta (superior o izquierdo) ha llegado a su límite inferior. Realice ajustes antes de hacer zoom out.";



catalog["信息提示"] = "Sugerencias";

catalog["日期"] = "Fecha";

catalog["标签页不能多于6个!"] = "No puede haber más de 6 pestañas.";
catalog["按部门查找"] = "Buscar por departamento";
catalog["选择部门下所有人员"] = "Seleccionar todos los usuarios del departamento";
catalog["(该部门下面的人员已经全部选择!)"] = "(Todo el personal en este departamento se han seleccionado.)";
catalog["按人员编号/姓名查找"] = "Buscar por usuario";
catalog["按照人员编号或姓名查找"] = "Buscar por usuario";
catalog["查询"] = "Buscar";
catalog["请选择部门"] = "seleccione un departamento";
catalog["该部门下面的人员已经全部选择!"] = "Todo el personal en este departamento se han seleccionado.";
catalog["打开选人框"] = "Abrir cuadro de selección";
catalog["收起"] = "Cerrar";
catalog["已选择人员"] = "Usuarios seleccionados ";
catalog["清除"] = "Borrar";
catalog["编辑还未完成，已临时保存，是否取消临时保存?"] = "La configuración no se ha completado todavía y se guarda temporalmente. ¿Desea cancelar el guardado temporal?";
catalog["恢复"] = "Restaurar";
catalog["会话已经过期或者权限不够,请重新登入!"] = "La sesión ha expirado o no tiene privilegios. Reinicie sesión.";

catalog["没有选择要操作的对象"] = "Seleccione un dispositivo";
catalog["进行该操作只能选择一个对象"] = "Solo un dispositivo puede ser seleccionado para esta operación";
catalog["相关操作"] = "Opciones Relacionadas";
catalog["共"] = "Total";
catalog["记录"] = "Registros ";
catalog["页"] = "Página ";
catalog["首页"] = "Primera";
catalog["前一页"] = "Anterior";
catalog["后一页"] = "Siguiente";
catalog["最后一页"] = "Última";
catalog["选择全部"] = "Todo";

catalog["January February March April May June July August September October November December"] = "Enero Febrero Marzo Abril Mayo Junio Julio Agosto Septiembre Octubre Noviembre Diciembre";
catalog["S M T W T F S"] = "D L M M J V S";

catalog["记录条数不能超过10000"] = "El máximo de eventos es de 10,000";
catalog["当天存在员工排班时"] = "había calendario previsto en el día actual";

catalog["暂无提醒及公告信息"] = "No hay recordatorios ni avisos";
catalog["关于"] = "Acerca de";
catalog["版本号"] = "Versión";
catalog["本系统建议使用浏览器"] = "Navegadores recomendados";
catalog["显示器分辨率"] = "Resolución del monitor";
catalog["及以上像素"] = "y más píxeles";
catalog["软件运行环境"] = "Entorno operativo para el funcionamiento de este software";
catalog["系统默认"] = "Valores por default";

catalog["photo"] = "Foto";
catalog["table"] = "Tabla";

catalog["此卡已添加！"] = "Esta tarjeta ya existe!";
catalog["卡号不正确！"] = "El número de tarjeta es incorrecto!";
catalog["请输入要添加的卡号！"] = "Ingrese el número de tarjeta!";
catalog["请选择刷卡位置！"] = "Seleccione el punto de lectura de tarjetas";
catalog["请选择人员！"] = "Seleccione un usuario.";
catalog["table"] = "Tabla";
catalog["table"] = "Tabla";
catalog["首字符不能为空!"]="El primer carácter no puede estar nulo.";
catalog["密码长度必须大于4位!"]="La contraseña debe ser de al menos 4 dígitos.";

catalog["当前列表中没有卡可供分配！"] = "No hay tarjetas disponibles para asignar en la lista actual.";
catalog["当前列表中没有人员需要分配！"] = "No hay necesidad de asignar tarjetas en la lista actual.";
catalog["没有已分配人员！"] = "No hay usuarios asignados.";
catalog["请先点击停止读取！"] = "Detenga la lectura de tarjetas.";
catalog["请选择需要分配的人员！"] = "Seleccione el usuario para asignar tarjeta.";

catalog["请选择一个介于1到223之间的数值！"] = "Ingrese un valor entre 1 y 223.";
catalog["备份路径不存在，是否自动创建？"] = "No existe la carpeta o ruta para guardar el respaldo. ¿Desea crearla?";
catalog["处理中"] = "Procesando..." ;
catalog["是"] = "Sí";
catalog["否"] = "No";


catalog["已登记指纹"] = "Huellas registradas:";

catalog["通讯密码"] = "Contraseña de comunicación";

catalog["您选择了[新增时删除设备中数据]，系统将自动删除设备中的数据(事件记录除外)，确定要继续？"] = "Seleccionó borrar datos en el dispositivo al agregar. Con ésta opción se borrarán los datos del dispostivo excepto la memoria de eventos. ¿Está seguro de continuar?";


//2012.5.11新增
catalog["'满足任意一个' 值域必须是以','隔开的多个值"] = "Sólo el múltiplo de valor dividido por', 'hacer frente a cualquier rango de valores'. ";
catalog["确认"] = "Aceptar";
catalog[" 已添加过波特率不为："] = "Baudios:";
catalog[" 的设备！同一个串口下不允许存在多个波特率不同的设备。请重新选择波特率！"] = "Solo puede agregar dispositivos con la misma velocidad de baudios. Seleccione los baudios correctamente.";
catalog["一体机，继续添加？"] = "dispositivo de control de acceso. ¿Está seguro de agregar?";
catalog["您没有选择[新增时删除设备中数据]，该功能仅用于系统功能演示和测试。请及时手动同步数据到设备，以确保系统中和设备中权限一致，确定要继续？"] = "La opción (borrar datos en el dispositivo al agregar) no se seleccionó. Deberá sincronizar los datos manualmente para el correcto funcionamiento del dispositivo.";
catalog["确定要清除命令队列？"] = "¿Está seguro de borrar la cola de comandos?";
catalog["清除缓存命令成功！请及时手动同步数据到设备，以确保系统中和设备中权限一致！"] = "El caché de comandos se han borrado con éxito. Sincronizace manualmente los datos en el dispositivo.";
catalog["权限组列表"] = "Lista de privilegios";
catalog["门列表"] = "Lista de puertas";
catalog["人员列表"] = "Lista de usuarios";
catalog["浏览 "]= "Examinando ";
catalog["可以进出的门"] = " Tiene privilegio de acceso a las puertas";
catalog["以人员查询"] = "Por usuarios";
catalog["以门查询"] = "Por puertas";
catalog["以权限组查询"] = "Por nivel de acceso";
catalog["当前门处于常开状态，是否禁用当天常开时间段后关门？"] = "El estado de la puerta es normalmente abierto. ¿Desea desactivar el horario de apertura programada después de cerrar?";
catalog["当前已常开"] = "Se encuentra normalmente abierta";
catalog["发送请求失败！"] = "Operación fallida!";
catalog["发送请求成功！"] = "Operación exitosa!";
catalog["发送请求失败，请重试！"] = "Operación fallida!";
catalog["禁用"] = "Deshabilitado";
catalog["当前设备状态不支持该操作！"] = "El estado actual del dispositivo no permite realizar la operación.";
catalog["该人员没有登记照片！"] = "El usuario no tiene foto registrada.";
catalog["设置定时获取记录时间"] = "Establecer la hora para la descarga de eventos nuevos";
catalog["每天"] = "Descargar eventos nuevos  ";//特殊翻译请核对页面
catalog[" 点自动从设备获取新记录"] = " el acceso automático a todo nuevo récord desde el dispositivo";
catalog["注：请确保服务器在设置的时间点处于开机状态。"] = "Tenga en cuenta Asegúrese de que el servidor está encendido durante el tiempo que el conjunto.";
catalog["定时下载记录时间设置成功！该设置将在软件服务或者操作系统重启后生效！"] = "Ajuste de la hora iniciar y operar de manera independiente de los ajustes entrarán en vigor después de reiniciar el software y el servicio o el sistema operativo";
catalog["定时下载记录事件设置失败！请重试！"] = "Configuración de hora fallida.";
catalog["请输入有效的时间点(0-23)！"] = "Ingrese una hora válida (0-23).";
catalog["无"] = "Ninguno";
catalog["注：1.请确保服务器在设置的时间点处于开机状态。<br/> 2.如需设置多个时间点，请以逗号分开。"] = "Nota: 1.Por favor asegúrese de que el servidor está encendido en el tiempo establecido <br/> 2 Para establecer múltiples puntos de tiempo, separados por comas...";
catalog["新增时删除设备中数据"] = "Borrar datos en el dispositivo al agregar.";
catalog[" 的设备添加失败！原因："] = " Falla al agregar el dispositivo. Causa:";
catalog["操作失败！原因："] = "Operación fallida. Causa:"; 
catalog["指纹模板错误，请重新登记！"] = "Error en la plantilla de la huellas digital. Registre la huella nuevamente!";
catalog["卡号"] = "Número de tarjeta";
catalog["统统计的时间可能会较长，请耐心等待"] = "Puede tardar un poco más. Espere por favor...";
catalog["地图宽度到达上限(1120px)，不能再放大！"] = "El ancho del mapa ha alcanzado el límite máximo (1120px). No es posible ampliar más la imagen.";
catalog["地图宽度到达下限(400px)，不能再缩小！"] = "El ancho del mapa ha alcanzado el límite mínimo (400px). No es posible reducir más la imagen.";
catalog["地图高度到达下限(100px)，不能再缩小！"] = "La altura del mapa ha alcanzado el límite mínimo (100px). No es posible reducir más la imagen.";
catalog["请输入大于0的数字"] = "Ingrese un número mayor que 0";
catalog["产品ID"] = "ID del producto";
catalog["不合法"] = "Inválido";
catalog["登记指纹功能只支持IE浏览器"] = "El registro de huellas digitales solo es compatible con Internet Explorer.";
catalog["请安装指纹仪驱动"] = "Instale el driver del lector de huellas";
catalog["解析xml文件出错"] = "Error al cargar achivo XML.";
catalog["该通道已达最大访问量！"] = "El canal ha alcanzado el máximo de usuarios";
catalog["当前没有可用的角色,请先添加角色"] = "No hay privilegios disponibles.";
catalog["当前设备IP地址和服务器不在同一网段，请先将其调整到一个网段，再尝试添加！"] = "El dispositivo y el servidor están segmentos de red diferentes. Ajuste los dispositivos al mismo segmento de red.";
catalog["数据库将备份到:"] = "El respaldo se guardara en la ruta:";
catalog["所选的部门总数不能大于2000"] = "Los departamentos seleccionados no puede exceder de 2000";
catalog["操作成功！"] = "Operación Exitosa!";
catalog["操作失败！"] = "Error en la operación";
catalog["服务器处理数据失败，请重试！错误码："] = "El servidor no puede procesar los datos Por favor, inténtelo de nuevo Código de error:";
catalog["请选择门禁设备，该功能仅针对门禁设备"] = "Por favor, elegir el equipo de control de acceso, esta función sólo para los equipos de control de acceso";
catalog["重连间隔时间必须为整数！"] = "El invervalo de la reconexión debe ser un valor numérico!";
catalog["设置成功，重启服务后生效！"] = "Operación exitosa. La configuración tomará efecto después de reiniciar los servicios del software o el sistema operativo.";
catalog["设置成功！"] = "Configurado correctamente!";
catalog["获取记录时间点不能为空！"] = "El tiempo de obtención de las nuevas entradas no puede estar vacío! ";
catalog["用户注册失败，请检查设备配置"] = "Conexión fallida. Revise la configuración del dispositivo."; 
catalog["目前该功能仅支持IE系列及IE内核的浏览器，请更换！"] = "Esta función solo es compatible con Internet Explorer";
catalog["请选择视频设备！"] = "Por favor, seleccione un dispositivo.";
catalog["控件初始化失败，请确定视频设备类型是否选择正确或重装控件！"] = "No se pudo inicializar el control ActiveX. Reinstale el controlador o revise la configuración ActiveX del Internet Explorer";
catalog["预览失败"] = "Vista previa fallida";

catalog["邮箱地址格式不正确"] = "Dirección de correo electrónico inválida";
catalog["请输入邮箱地址"] = "Ingrese la dirección de correo electrónico";
catalog["邮件通知"] = "Notificación por correo electrónico";
catalog["报警监控"] = "Monitoreo de alarma";
catalog["辅助输入"] = "Entrada de alarma";
catalog["辅助输出"] = "Salida de alarma";
catalog["邮件通知"] = "Notificación por correo electrónico";
catalog["请输入邮箱地址"] = "Ingrese la dirección de correo electrónico";
catalog["请输入邮箱地址，多个地址用 ';' 隔开"] = "Ingrese la dirección de correo electrónico. Para agregar más correos utilize punto y coma (;) para separarlos";
catalog["邮件发送成功!"] = "Correo enviado con éxito!";
catalog["邮件发送失败!"] = "Envío de correo electrónico fallido!";
catalog["邮件发送失败,门禁参数配置中邮箱配置错误!"] = "Envío de correo electrónico fallido. La configuración de los parámetros de correo es incorrecta";

catalog["请选择报警设备!"] = "Seleccione el dispositivo de alarma";
catalog["门状态"] = "Estado de la puerta";
catalog["门锁状态"] = "Estado del relevador";
catalog["门关报警"] = "Alarma de puerta cerrada";
catalog["门开报警"] = "Alarma de puerta abierta";
catalog["门开超时"] = "Puerta mantenida abierta";
catalog["解锁"] = "Abierto";
catalog["锁定"] = "Cerrado";
catalog["没有报警"] = "Sin alarma";
catalog["防拆"] = "Tamper";
catalog["胁迫密码开门"] = "Apertura con contraseña de amago";
catalog["胁迫指纹开门"] = "Apertura con huella de de amago";
catalog["门被意外打开"] = "Puerta forzada";
catalog["请先关闭门！"] = "Cierre la puerta!";
catalog["胁迫开门"] = "Apertura por amago";


catalog["视频服务器登录失败，请确认后重试！原因："] = "No se pudo conectar al servidor de video. Intente de nuevo. Razón: ";
catalog["视频服务器登录失败，请确认后重试！错误码："] = "No se pudo conectar al servidor de video. Código de error:";
catalog["视频回放失败，请确认后重试！原因："] = "No se pudo reproducir el vídeo. Intente de nuevo. Razón:";
catalog["视频回放失败，请确认后重试！错误码："] = "No se pudo reproducir el vídeo. Intente de nuevo. Código de error:";
catalog["视频服务器登录失败，请确认后重试！"] = "No se pudo conectar al servidor de video. Intente de nuevo."
catalog["当前系统中没有添加视频服务器，请添加！"] = "No hay dispositivos de video agregados.";
catalog["视频通道不能重复选择，请重新选择！"] = "No se puede utilizar el mismo canal de video. Seleccione otro canal.";
catalog["读头"] = "Lector";
catalog["名称"] = "Nombre";
catalog["视频时长不能小于0，请输入正确的视频时长!"] = "El intervalo de visualización de vídeo no puede ser inferior a los 0, por favor, introduzca la la!";
catalog["录像时长不能小于0，请输入正确的录像时长!"] = "El intervalo de grabación de vídeo no puede ser inferior a los 0, por favor, introduzca el correcto!";
catalog["添加摄像机到当前地图"] = "Agregar una cámara al mapa";
catalog["请选择要添加的摄像头！"] = "Seleccione la cámara que desea agregar";
catalog["视频查询"] = "Búsqueda de video";
catalog["视频联动"] = "Vínculo de video";
catalog["视频加载中，请稍侯......"] = "Cargando video, espere por favor...";
catalog["该通道已达最大访问量或视频服务器未连接!"] = "Este canal de video ha superado el máximo de conexiones o no está conectado";
catalog["预览失败，请确认后重试！原因："] = "Vista previa fallida. Intente de nuevo. Razón: ";
catalog["预览失败，请确认后重试！错误码："] = "Vista previa fallida. Intente de nuevo. Código de error: ";
catalog["无此权限！"] = "Sin privilegio";
catalog["没有录像文件！"] = " No hay archivos de vídeo! ";
catalog["该通道已达最大访问量或视频服务器未连接！"] = "Este canal de video ha superado el máximo de conexiones o no está conectado";
catalog["从视频服务器导出失败！"] = "Exportación de video fallida!";
catalog["从视频服务器导出成功！"] = "Exportación de video realizada exitosamente!";
catalog["视频弹出窗口高度必须为整数！"] = "La altura de la ventana de pop-up debe ser un número entero!";
catalog["请选择需要设置的对象!"] = "Seleccione los objetos que requiera configurar!";
catalog["请启用当前视频设备下被禁用的视频通道！"] = "Habilite los canales de video del dispositivo de video!";
catalog ["HIKVISION_ERROR_0"] = "Error desconocido.";
catalog ["HIKVISION_ERROR_1"] = "usuario o contraseña incorrecta.";
catalog ["HIKVISION_ERROR_4"] = "Número de canal incorrecto";
catalog ["HIKVISION_ERROR_5"] = "Ha superado el número máximo de usuarios simultaneos para conectarse al DVR.";
catalog ["HIKVISION_ERROR_7"] = "Conexión al DVR fallida.";
catalog ["HIKVISION_ERROR_8"] = "No se pudo enviar datos al DVR.";
catalog ["HIKVISION_ERROR_17"] = "Parámetro incorrecto.";
catalog ["HIKVISION_ERROR_19"] = "No hay disco duro.";
catalog ["HIKVISION_ERROR_20"] = "Error de disco duro.";
catalog ["HIKVISION_ERROR_21"] = "El disco duro está lleno.";
catalog ["HIKVISION_ERROR_22"] = "Error en el disco duro.";
catalog ["HIKVISION_ERROR_24"] = "Servidor ocupado.";
catalog ["HIKVISION_ERROR_28"] = "Falta de recursos del DVR.";
catalog ["HIKVISION_ERROR_29"] = "Operación fallida del DVR";
catalog ["HIKVISION_ERROR_33"] = "El DVR no tiene el archivo especificado durante la reproducción.";
catalog ["HIKVISION_ERROR_36"] = "La última operación aún no ha terminado.";
catalog ["HIKVISION_ERROR_38"] = "Error de reproducción.";
catalog ["HIKVISION_ERROR_46"] = "El número máximo.";
catalog ["HIKVISION_ERROR_47"] = "El usuario no existe.";
catalog ["HIKVISION_ERROR_52"] = "Máximo número de usuarios.";
catalog ["HIKVISION_ERROR_74"] = "ID de usuario en la cancelación de someterse a una operación.";
catalog ["HIKVISION_ERROR_90"] = "El dispositivo está siendo respaldado.";

catalog["许可信息"] = "Información de licencia";
catalog["请选择每个扩展板的继电器数量！"] = "Seleccione el número de relevadores de cada tarjeta de expansión!";
catalog["请切换为英文输入法状态！"] = "Cambie la entrada de datos a Inglés!";

//登录页面验证
catalog["比对验证中，请稍等!"] = "Verificando, por favor espere...";
catalog["验证失败，请重试!"] = "Verificación fallida, intente de nuevo!";
catalog["10.0指纹算法许可失败!"] = "La licencia del algoritmo v10.0 de huellas digitales no pudo verificarse.";
catalog["验证通过，登录系统!"] = "Verificado correctamente... Iniciando sesión en el sistema!";
catalog["获取指纹失败，请重试!"] = "No se pudo leer la huella, intente de nuevo por favor!";
catalog["登记指纹功能只支持IE浏览器"] = "La función de inicio con huella digital solo es compatible con Internet Explorer.";
catalog["请安装指纹仪驱动"] = "Instale el driver del lector de huella USB";

//访客
catalog["进入地点"] = "Lugar de entrada";
catalog["离开地点"] = "Lugar de salida";
catalog["被访人姓名"] = "Nombre visitante";
catalog["被访人姓氏"] = "Apellido del visitante";
catalog["是否重新打印访客单？"] = "¿Volver a imprimir visitante?";
catalog["没有注册读写器控件，是否下载控件？"] = "No tiene ningún dispositivo registrado. Conecte un dispositivo e instale el driver.";
catalog["没有注册扫描仪控件，是否下载控件？"] = "No tiene ningún escáner registrado. Conecte un escáner e instale el driver.";
catalog["暂时不支持该证件类型！"] = "El tipo de documento no es soportado.";
catalog["请选择正确的证件类型或调整证件的位置！"] = "Seleccione el tipo de documento o configure la ubicación del documento.";
catalog["加载核心失败！"] = "Operación fallida!";
catalog["初始化失败！"] = "Inicialización fallida!";
catalog["请放好身份证！"] = "Presente la identificación";
catalog["没有检测到身份证阅读器！"] = "No se detecto el lector de tarjetas de identificación.";
catalog["目前该功能仅支持二代身份证！"] = "Esta función solo es compatible con la segunda generación de tarjetas!";
catalog["没有可选的权限组！"] = "No hay niveles de acceso para visitantes";
catalog["卡号已存在，如果确认将重新发卡，请先清除该卡原持卡人"] = "El número de la tarjeta ya existe. Si desea volver a emitir una tarjeta, primero elimine el usuario original de la tarjeta ";
catalog["临时"] = "Temporal";
catalog["get_visit_state"] = "Estado";

//init_base_frame.js
catalog["正式版许可"] = "La versión oficial de la licencia";
catalog["试用版许可"] = "Licencia Trial";

//faltantes
catalog["Save and New"]="Guardar y Agregar Nuevo";
catalog["OK"] = "OK";
catalog["Cancel"] = "Cancelar";

catalog["断开"] = "Desconectado";
catalog["短路"] = "En cortocircuito";

//Employee_edit.html
catalog["没有可选的梯控权限组！"] = "Sin la opción de Ascensor Nivel!";

//Dev_RTMonitor.html
catalog["请先停止监控再导出！"] = "Por favor, dejen de vigilancia antes de la exportación!";
catalog["服务未启动"] = "El servicio no Correr";
catalog["门禁服务未启动，请先点击左方启动服务按钮"]= "El servicio no está activo. De click en 'Iniciar servicio' para iniciar el servicio";
catalog["门禁服务开启成功！"] = "Iniciar el servicio de acceso con éxito!";
catalog["邮箱测试发送成功！"] = "Prueba de envió de correo electrónico con éxito!";
catalog["接收者邮箱地址格式不正确！"] = "Direcciones de correo no válida para recibir!";
catalog["请选择开始时间"] = "Por favor, seleccione la hora de inicio";
catalog["请选择结束时间"] = "Por favor, seleccione la hora de finalización";
catalog["只能查询3个月内的数据"] = "Sólo los datos de la consulta plazo de tres meses";
catalog["只能查询2个月内的数据"] = "Sólo los datos de la consulta en los dos meses";
catalog["只能查询1个月内的数据"] = "Sólo los datos de la consulta dentro de un mes";

//in file--D:\trunk\units\adms\mysite\ Acc_Option.html
catalog["发件人邮箱地址格式不正确"] = "Dirección del buzón tiene un formato incorrecto";
catalog["收件人邮箱地址格式不正确"] = "Dirección del destinatario tiene un formato incorrecto";
catalog["请输入邮件服务器(SMTP)地址"] = "Por favor ingrese servidor de buzones (SMTP)";
catalog["服务器端口只能为数字"] = "Puerto del servidor sólo puede ser un valor numérico";
catalog["服务器端口不能为0"] = "Puerto del servidor no puede ser 0";
catalog["夏令时时间只能为数字！"] = "El tiempo de DST sólo puede ser una numérico!";
catalog["只支持导入Excel文件！"] = "Sólo el soporte de archivos de Excel!";
catalog["请选择要测试的门！"] = "Por favor, elija la puerta de pruebas!";

