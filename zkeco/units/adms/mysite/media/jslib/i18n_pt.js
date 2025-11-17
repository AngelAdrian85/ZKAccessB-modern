___f=function(){
jQuery.validator.messages.required="Obrigatório"
jQuery.validator.messages.email="Não é um email válido"
jQuery.validator.messages.date="Por favor, insira uma data válida: aaaa/mm/dd."
jQuery.validator.messages.dateISO="Por favor, insira uma data válida (ISO): aaaa-mm-dd."
jQuery.validator.messages.wZBaseDateField="Por favor, insira uma data válida: aaaa-mm-dd."
jQuery.validator.messages.wZBaseDateTimeField="Por favor, insira uma data válida: aaaa-mm-dd hh:mm:ss."
jQuery.validator.messages.wZBaseTimeField="Por favor, insira um horário válido: hh:mm:ss."
jQuery.validator.messages.wZBaseIntegerField="Por favor, insira um número inteiro."
jQuery.validator.messages.number="Por favor, insira um valor válido."
jQuery.validator.messages.digits="Somente valores numéricos"
jQuery.validator.messages.equalTo="Diferente"
jQuery.validator.messages.minlength=$.validator.format("pelo menos {0} caractere(s)")
jQuery.validator.messages.maxlength=$.validator.format("no máximo {0} caractere(s)")
jQuery.validator.messages.rangelength=$.validator.format("entre {0} e {1} caractere")
jQuery.validator.messages.range=$.validator.format("entre {0} e {1}")
jQuery.validator.messages.max=$.validator.format("Por favor, insira um valor menor que {0}.")
jQuery.validator.messages.min=$.validator.format("Por favor, insira um valor maior que {0}.")
jQuery.validator.messages.xPIN="somente são permitidos valores numéricos ou letras"
jQuery.validator.messages.xNum="somente números são permitidos"
jQuery.validator.messages.xMobile="Número de celular incorreto."
jQuery.validator.messages.xTele="Número de telefone fixo incorreto"
jQuery.validator.messages.xSQL="\" ou \' não são permitidos."
}
___f();

if(typeof(catalog)=="undefined") {catalog={}}

catalog["请选择一个字段"] = "Por favor, selecione um campo.";
catalog["输入的值错误"] = "Valor inserido incorreto";
catalog["确定注销系统?"] = "Tem certeza que deseja sair do sistema?";
catalog["通讯失败"] = "Falha";
catalog["确定"] = "Confirma";
catalog["日志"] = "Logs";
catalog["请选择一条历史备份记录!"] = "Por favor, selecione uma entrada de backup de histórico.";
catalog["还原成功!"] = "Restaurado com êxito";
catalog["间隔时间不能超过一年"] = "O intervalo não pode exceder 1 ano.";
catalog["间隔时间不能小于24小时"] = "O intervalo não pode ser menor que 24horas.";
catalog["在当前时间的一个小时内只能备份一次"] = "O backup pode ser feito somente uma vez dentro de uma hora do horário atual.";
catalog["请先在服务控制台中设置数据库备份路径"] = "Por favor, configure o caminho de backup do banco de dados no console de serviço antes.";
catalog["全部"] = "Tudo";
catalog["数据格式必须是json格式!"] = "O dado deve estar no formato json.";
catalog["修改密码"] = "Modificar Senha";
catalog["旧密码："] = "Senha Antiga:";
catalog["新密码："] = "Senha Nova:";
catalog["确认密码："] = "Confirmar Senha:";
catalog["最大6位整数"] ="máx. 6-dígitos";
catalog["人员编号必须为数字"] = "O número da pessoa deve ser numérico.";
catalog["图片格式无效!"] = "Formato de figura inválido";
catalog["请输入有效的E_mail!"] ="Por favor, insira um e-mail válido!";
catalog["身份证号码不正确"] = "Número de ID de cartão inválido";
catalog["指纹模板错误，请立即联系开发人员！"] = "Há erro na imagem do dedo, entre em contato conosco o mais rapido possível!";
catalog["设备名称不能为空"] = "O nome do equipamento não pode estar em branco.";
catalog["设备序列号不能为空"] = "O número de série do equipamento não pode estar em branco.";
catalog["通讯密码必须为数字"] = "A senha de comunicação deve conter somente números.";
catalog["请输入一个有效的IPv4地址"] = "Por favor, insira um endereço de IPv4 válido.";
catalog["请输入一个有效的IP端口号"] = "Por favor, insira um número válido de porta de IP";
catalog["请输入一个RS485地址"] = "Insira um endereço RS485.";
catalog["RS485地址必须为1到63之间的数字"] = "O endereço RS485 deve ter um número entre 1 e 63.";
catalog["请选择串口号"] = "Por favor, selecione um número da porta serial.";
catalog["请选择波特率"] = "Por favor, selecione um baud rate.";
catalog["请选择设备所属区域"] = "Por favor, selecione uma área para o equipamento.";
catalog["串口：COM"] = "Porta Serial COM";
catalog[" 的RS485地址："] = "'s RS485 address";
catalog[" 已被占用！"] = " está ocupado!";
catalog["后台通讯忙，请稍后重试！"] = "A comunicação está ocupada, por favor, tente mais tarde!";
catalog["门控制器，继续添加？"] = "porta(s) do painel de controle. Continua a adição?";
catalog["提示：设备连接成功，确定后将添加设备！"] = "Nota: O equipamento está conectado com êxito, e os tipos dos paineis de controle de acesso estão corretos. Adicione o equipamento após a confirmação!";
catalog["提示：设备连接失败（错误码："] = "Nota: Falha de conexão do equipamento (Cód. erro:";
catalog["），确定添加该设备？"] = "). Tem certeza que deseja adicionar o equipamento?";
catalog["提示：设备连接失败（原因："] = "Nota: O equipamento não mantém conexão (causa: ";
catalog["您选择了[新增时删除设备中数据]，系统将自动删除设备中的数据(事件记录除外)，确定要继续？"] = "Selecione [Limpar dados no dispositivo ao Adicionar], o sistema irá apagar os dados (exceto o log de eventos) no dispositivo, Continuar?";
catalog["您没有选择[新增时删除设备中数据]，该功能仅用于系统功能演示和测试。请及时手动同步数据到设备，以确保系统中和设备中权限一致，确定要继续？"] = "Não selecione [Limpar dados no dispositivo ao Adicionar], esta função só é usada para demonstração e testes do sistema. Por favor, sincronize os dados para o dispositivo manualmente, para garantir a consistência dos dados do sistema e dispositivo, Continuar ?";
catalog["编辑设备信息("] =  "editar informação do equipamento.";
catalog["对不起，您没有访问该页面的权限，不能浏览更多信息！"] = "Desculpe, você não tem permissão para visualizar essa página, então não é possível ver as informações!";
catalog["确定要清除命令队列？"] = "Você tem certeza que deseja apagar a lista de comandos?";
catalog["清除缓存命令成功！请及时手动同步数据到设备，以确保系统中和设备中权限一致！"] = "Os comandos de cache foram apagadas com sucesso! Por favor, sincronize os dados para o dispositivo manualmente, para garantir a consistência dos dados do sistema e do dispositivo!";
catalog["清除缓存命令失败!"] = "Os comandos de cache não foram apagados com êxito!";
catalog["显示部门树"] = "Mostrar árvore de departamento";
catalog["隐藏部门树"] = "Esconder árvore de departamento";
catalog["请选择一个调动栏位"] = "Por favor, selecione uma posição de transferência.";
catalog["部门花名册"] = "lista de departamento";
catalog["学历构成分析表"] = "análise da composição da educação";
catalog["人员流动表"] = "relatório de movimentação das pessoas";
catalog["人员卡片清单"] = "lista de cartões das pessoas";
catalog["请选择开始日期和结束日期"] = "Por favor, selecione a data de início e a final.";
catalog["开始日期不能大于结束日期"] = "A data de início não pode ser depois da data final.";
catalog["每次发卡数量不能超过100"] = "Máximo 100 cartões podem ser emitidos ao mesmo tempo.";
catalog["起始编号长度不能超过"] = "O comprimento do número inicial não pode ser excedido";
catalog["位"] = " dígitos.";
catalog["结束编号长度不能超过"] = "O comprimento do número final não poder ser excedido";
catalog["起始人员编号与结束人员编号的长度位数不同！"] = "O No. inicial e o final possuem comprimentos diferentes.";
catalog["点击查看消息详情"] = "Clique para ver detalhes da mensagem";
catalog["删除该消息"] = "Apagar essa mensagem";
catalog["公告详情"] = "Detalhes do Aviso";
catalog["保存成功!"] = "Salvo com êxito";
catalog["人员选择:"] = "Selecione uma pessoa:";
catalog["人员查询"] = "busca de pessoa";
catalog["人员编号"] = "No. da pessoa";
catalog["姓名"] = "Nome";
catalog["身份证号查询"] = "Busca do número do cartão ID";
catalog["身份证号码"] = "Número do cartão ID";
catalog["考勤设备查询"] = "busca do equipamento de registro";
catalog["离职人员查询"] = "Busca das pessoas que saíram";
catalog["考勤原始数据查询"] = "busca nos dados dos registro das marcações originais";
catalog["员工调动查询"] = "busca de transferência de pessoas";
catalog["卡片查询"] = "busca do cartão";
catalog["部门查询"] = "busca do departamento";
catalog["部门编号"] = "número do departamento";
catalog["部门名称"] = "nome do departamento";
catalog["补签卡查询"] = "busca de log de adição";
catalog["服务器加载数据失败,请重试!"] = "Falha no servidor para carregar os dados. Por favor, tente novamente.";
catalog["结束日期不能大于今天"] = "A data final não pode ultrapassar o dia de hoje.";
catalog["统计只能当月日期，或者天数不能超过开始日期的月份天数！ "] = "As estatísticas envolvem somente as datas do mês, ou o número de dias envolvidos não podem exceder o número de dias contido no mês da data inicial.";
catalog["统统计的时间可能会较长，请耐心等待"] = "Estatísticas do tempo pode ser maior, por favor, seja paciente";
catalog["请选择人员或部门"] = "Por favor, selecione a pessoa ou departamento.";
catalog["统计结果详情"] = "resultado da estatística";
catalog["请选择开始日期或结束日期!"] = "Por favor, selecione uma data de início ou final.";
catalog["开始日期不能大于结束日期!"] = "A data de início não pode ultrapassar a data final.";
catalog["最多只能查询31天的数据!"] = "No máximo 31 dias de dados podem ser procurados.";
catalog["请在查询结果中选择人员！"] = "Por favor, selecione uma pessoa do resultado da busca.";
catalog["取消"] = "cancelar";
catalog["展开"] = "Desdobrar";
catalog["收缩"] = "Dobrar";
catalog["自定义工作面板"] = "Customizar Painel de trabalho";
catalog["锁定"] = "travar";
catalog["解除"] = "destravar";
catalog["常用操作"] = "Operação Diária";
catalog["常用查询"] = "Busca Comum";
catalog["系统提醒、公告"] = "Lembrete e Notificação do Sistema";
catalog["人力构成分析"] = "Análise da Composição das Pessoas";
catalog["加载中......"] = "carregando...";
catalog["是否"] = "Sim/Não";
catalog["选择所有 {0}(s)"] = "Selecionar tudo {0}(s)";
catalog["选择 {0}(s): "] = "Selecionar {0}(s):";
catalog["服务器处理数据失败，请重试！"] = "Falha no processamento de dados no servidor. Por favor, tente novamente!";
catalog["新建相关数据"] = "Gerar dados relacionados";
catalog["浏览相关数据"] = "Pesquisar dados relacionados";
catalog["添加"] = "Adic.";
catalog["浏览"] = "Buscar";
catalog["编辑"] = "Editar";
catalog["编辑这行数据"] = "editar essa linha ";
catalog["升序"] = "Crescer";
catalog["降序"] = "Decrescer";
catalog["该模型不支持高级查询功能"] = "Esse modelo não suporta funções avançadas de pesquisa.";
catalog["高级查询"] = "Pesquisa Avançada";
catalog["导入"] = "Importar";
catalog["请选择一个上传的文件!"] = "Por favor, selecione o arquivo para enviar.";
catalog["标题行号必须是数字!"] = "O título do número da linha deve ser numérico.";
catalog["记录行号必须是数字!"] = "A entrada do número da linha deve ser numérico.";
catalog["请选择xls文件!"] = "Por favor, selecione um arquivo xls.";
catalog["请选择csv文件或者txt文件!"] = "Por favor, selecione um arquivo .csv ou .txt";
catalog["文件标头"] = "cabeçalho do arquivo";
catalog["文件记录"] = "registro do arquivo";
catalog["表字段"] = "campo da tabela";
catalog["请先上传文件！"] = "Por favor, faça o upload do arquivo antes."
catalog["导出"] = "Exportar";
catalog["页记录数只能为数字"] = "A quantidade de entrada nas páginas somente pode ser numérica.";
catalog["页码只能为数字"] = "O número de páginas somente pode ser numérico.";
catalog["记录数只能为数字"] = "A quantidade de entrada somente pode ser numérica.";
catalog["用户名"] = "Nome do usuário";
catalog["动作标志"] = "Sinal de ação";
catalog["增加"] = "Adicionar";
catalog["修改"] = "Modificar";
catalog["删除"] = "Apagar";
catalog["其他"] = "Outros";
catalog["信息提示"] = "Notas";
catalog["日期"] = "data";
catalog["标签页不能多于6个!"] = "Não podem haver mais que 6 abas.";
catalog["按部门查找"] = "Procura por Departamento";
catalog["选择部门下所有人员"] = "Selecionar todas as pessoas do Departamento";
catalog["(该部门下面的人员已经全部选择!)"] = "(Todas as pessoas dentro desse departamento foram selecionadas.)";
catalog["按人员编号/姓名查找"] = "Procura por No./Nome da pessoa";
catalog["按照人员编号或姓名查找"] = "Procura por No./Nome da pessoa";
catalog["查询"] = "procura";
catalog["请选择部门"] = "selecione departamento";
catalog["该部门下面的人员已经全部选择!"] = "Todas as pessoas dentro desse departamento foram selecionadas.";
catalog["打开选人框"] = "abrir a caixa de seleção";
catalog["收起"] = "Fechar";
catalog["已选择人员"] = "Pessoa selecionada ";
catalog["清除"] = "Limpar";
catalog["编辑还未完成，已临时保存，是否取消临时保存?"] = "A edição ainda não está completa, e foi salvo um arquivo temporário. Você deseja cancelar o salvamento temporário?";
catalog["恢复"] = "Restaurar";
catalog["会话已经过期或者权限不够,请重新登入!"] = "A sessão expirou ou sua permissão é limitada. Por favor, faça o login novamente.";
catalog["没有选择要操作的对象"] = "Não foi selecionado nenhum objeto para a operação";
catalog["进行该操作只能选择一个对象"] = "Somente um objeto pode ser selecionado para essa operação";
catalog["相关操作"] = "Operação relacionada";
catalog["共"] = "Total";
catalog["记录"] = "Entrada";
catalog["页"] = "Página";
catalog["首页"] = "Primeiro";
catalog["前一页"] = "Anterior";
catalog["后一页"] = "Próximo";
catalog["最后一页"] = "Último";
catalog["选择全部"] = "Tudo";
catalog["January February March April May June July August September October November December"] = "Janeiro Fevereiro Março Abril Maio Junho Julho Agosto Setembro Outubro Novembro Dezembro";
catalog["S M T W T F S"] = "D S T Q Q S S";
catalog["记录条数不能超过10000"] = "o máx. é 10000";
catalog["请输入大于0的数字"] = "Por favor insira um número maior que 0";
catalog["暂无提醒及公告信息"] = "Sem lembrete ou aviso";
catalog["关于"] = "Sobre ";
catalog["版本号"] = "Número da Versão";
catalog["本系统建议使用浏览器"] = "Os browsers que nós recomendamos";
catalog["显示器分辨率"] = "Resolução do monitor";
catalog["及以上像素"] = "pixels e acima";
catalog["软件运行环境"] = "O ambiente para executar esse software";
catalog["系统默认"] = "Padrão";
catalog["photo"] = "Foto";
catalog["此卡已添加！"] = "Esse cartão já foi adicionado!";
catalog["卡号不正确！"] = "Número de cartão incorreto!";
catalog["请输入要添加的卡号！"] = "Por favor, insira o número do cartão!";
catalog["请选择刷卡位置！"] = "Por favor, selecione a posição para aproximar o cartão!";
catalog["请选择人员！"] = "Selecione uma pessoa!";
catalog["table"] = "Tabela";
catalog["首字符不能为空!"] ="O primeiro caractere não pode ser vazio!";
catalog["密码长度必须大于4位!"] ="A senha deve possuir mais que 4 caracteres!";
catalog["当前列表中没有卡可供分配！"] = "Não há cartão a ser atribuído na lista atual!";
catalog["当前列表中没有人员需要分配！"] = "Não há pessoas que precisam da atribuição de cartão na lista atual!";
catalog["没有已分配人员！"] = "Não há nenhuma pessoa que tenha sido atribuída!";
catalog["请先点击停止读取！"] = "Por favor, pare e leia o número de cartão antes.";
catalog["请选择需要分配的人员！"] = "Por favor, selecione a pessoa que necessita atribuir o cartão!";
catalog["请选择一个介于1到223之间的数值！"] = "Por favor, especifique um valor entre 1 e 223!";
catalog["备份路径不存在，是否自动创建？"] = "O caminho de backup não existe, deseja criar automaticamente?";
catalog["处理中"] = "Processando";
catalog["是"] = "Sim";
catalog["否"] = "Não";
catalog["已登记指纹"] = "Impr. digital cadastrada:"
catalog["不合法"] ="Ilegal";
catalog["通讯密码"] = "Senha de Comunicação";
catalog["登记指纹功能只支持IE浏览器"] = "Funcao suporta apenas Navegador de Internet.";
catalog["请安装指纹仪驱动"] = "Por favor Instale os Drivers do leitor de Impressão Digital.";
catalog["解析xml文件出错"] = "Falha ao carregar xml!";
catalog["该通道已达最大访问量！"] = "O número de visitantes atingiu o valor máximo!";
catalog["当前没有可用的角色,请先添加角色"] = "Não há função disponível para escolher agora, por favor crie uma ou mais funções primeiro!";
catalog["当前设备IP地址和服务器不在同一网段，请先将其调整到一个网段，再尝试添加！"] = "Dispositivo e servidor estão em redes diferentes, configure-os na mesma rede e tente novamente!";
catalog["数据库将备份到:"] ="O banco de dados será copiado para:";
catalog["日期格式输入错误"] = "Formato da data inválido";
catalog["日期格式不正确！"] = "O formato da data está inválido!";
catalog["起始时间不能和结束时间相等！"] = "Os horários de início e de fim não podem ser o mesmos.";
catalog["提示：设备连接成功，但控制器类型与实际不符，将修改为"] = "Dica: Conexão com dispositivo realizada com sucesso, porém existe inconsistencia com o tipo atual de controlador, será modificado para ";

catalog["删除开门人员"] = "Apagar uma pessoa com acesso";
catalog["请先选择要删除的人员！"] = "Primeiro selecione a pessoa a ser removida.";
catalog["确认要从首卡常开设置信息中删除开门人员？"] = "Tem certeza que deseja apagar a informação da pessoa com acesso do primeiro conjunto de informação de cartão sempre-aberto?";
catalog["当前门:"] = "Porta atual:";
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行反潜设置！"] = "Falha na obtenção do parâmetro de extensão do equipamento atual selecionado, então a configuração do Anti-passback está indisponível para o equipamento.";
catalog["读取到错误的设备信息，请重试！"] = "Informação incorreta recebida do equipamento. Por favor, tente novamente!";
catalog["或"] = " ou ";
catalog["读头间反潜"] = "Anti-Passback entre os leitores";
catalog["反潜"] = "Anti-Passback";
catalog["请选择地图！"] = "Por favor, selecione um mapa!";
catalog["图片格式无效！"] = "Formato de foto inválido!";
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行互锁设置！"] = "Falha na obtenção do parâmetro de extensão do equipamento atual selecionado, então a configuração de intertravamento está indisponível para o equipamento.";
catalog["门:"] = "Porta: ";
catalog["与"] = "e";
catalog["互锁"] = "Intertravamento";
catalog["数据下载进度"] = "Progresso do recebimento dos dados";
catalog["设备名称"] = "Nome do equipamento";
catalog["总进度"] = "Progresso total";
catalog["当前选择设备的扩展参数获取失败，无法对该设备进行联动设置！"] = "Falha na obtenção do parâmetro de extensão do equipamento atual selecionado, então a configuração de combinação está indisponível para o equipamento.";
catalog["请输入联动设置名称！"] = "Por favor, insira um nome para a configuração de combinação.";
catalog["浏览多卡开门人员组："] = "Procure o Grupo de pessoas com acesso de Multi-cartão:";
catalog[" 的人员"] = "membro";
catalog["当前不存在多卡开门人员组"] = "Não há grupo de pessoas com acesso de Multi-cartão no momento.";
catalog["删除人员"] = "Apagar uma pessoa";
catalog["确认要从多卡开门人员组中删除人员？"] = "Tem certeza que deseja apagar essa pessoa do Grupo de pessoas com acesso de Multi-Cartão?";
catalog["请至少在一个组内填入开门人数！"] = "Por favor, insira um número de pessoas com acesso em pelo menos um grupo.";
catalog["至少两人同时开门！"] = "Pelo menos duas pessoas podem abrir a porta ao mesmo tempo!";
catalog["最多五人同时开门！"] = "No máximo 5 pessoas podem abrir a porta ao mesmo tempo!";
catalog["人"] = "Pessoa";
catalog["您还没有设置多卡开门人员组！请先添加！"] = "Você não configurou nenhum Grupo de pessoas com acesso de Multi-Cartão. Por favor, adicione um grupo antes.";
catalog["请在文本框内输入有效的时间！"] = "Por favor, digite um horário válido no campo.";
catalog["对不起,您没有韦根卡格式设置的权限,不能进行当前操作！"] = "Desculpe, você não tem permissão para configurar o formato do cartão Wiegand, então não é possível realizar a operação atual.";
catalog["添加门到当前地图"] = "Adicione as portas no mapa atual.";
catalog["请选择要添加的门！"] = "Por favor, selecione as portas que deseja adicionar!";
catalog["确定要删除当前电子地图："] = "Confirma a remoção do mapa atual?";
catalog["浏览人员："] = "Procurar pessoas:";
catalog[" 所属权限组"] = " nível de acesso";
catalog["当前不存在人员"] = "Nenhuma pessoa agora";
catalog["删除所属权限组"] = "Apagar nível de acesso";
catalog["请先选择要删除的权限组！"] = "Por favor, selecione o nível de acesso a ser apagado.";
catalog["确认要删除人员所属权限组？"] = "Tem certeza que deseja apagar o nível de acesso?";
catalog["数据处理进度"] = "Progresso do processamento de dados";
catalog["浏览权限组："] = "Procurar nível de acesso ";
catalog[" 的开门人员"] = " pessoa com acesso";
catalog["当前不存在权限组"] = "Nenhum nível de acesso agora";
catalog["从权限组中删除"] = "Apagar do nível de acesso";
catalog["权限组列表"] ="Lista de Nível de Acesso";
catalog["门列表"] = "Lista de portas"
catalog["人员列表"] = "Lista de Usuários"
catalog["浏览 "] = "Pesquisar "
catalog["可以进出的门"] = " Possuir nível de acesso"
catalog["当前不存在人员"] = "Nenhuma pessoa agora";
catalog["以人员查询"] = "Por usuário"
catalog["以门查询"] = "Por porta"
catalog["以权限组查询"] = "Por Nível de Acesso"
catalog["确认要从权限组中删除人员？"] = "Tem certeza que deseja remover a pessoa do nível de acesso?";
catalog["远程开门"] = "Abertura remota";
catalog["选择开门方式"] = "Escolha o modo de abertura da porta";
catalog["开门："] = "Abrir a porta para ";
catalog[" 秒"] = " Segundos(s)";
catalog["常开"] = "Normal aberto";
catalog["启用当天常开时间段"] = "Habilitar período de tempo intradiário normal aberto";
catalog["远程关门"] = "Fechamento remoto";
catalog["选择关门方式"] = "Escolha o modo de fechamento da porta";
catalog["关门"] = "Fechar a porta";
catalog["禁用当天常开时间段"] = "Desabilitar período de tempo intradiário normal aberto";
catalog["当前没有符合条件的门！"] = "Não existe porta que atendam essas condições.";
catalog["请输入有效的开门时长！必须为1-254间的整数！"] = "Por favor, digite um intervalo válido para abertura de porta! Deve ser um valor inteiro entre 1-254!";
catalog["禁用"] = "Desativar";
catalog["离线"] = "Desconectado";
catalog["报警"] = "Alarme";
catalog["门开超时"] = "Tempo esgotado de abertura";
catalog["关闭"] = "Fechado";
catalog["打开"] = "Aberto";
catalog["无门磁"] = "Sem sensor da porta";
catalog["导出报表"] = "Exportar Relatório";
catalog["设置定时获取记录时间"] = "Definir a hora para obter novas entradas";
catalog["每天"] = "Obter novas entradas ";//特殊翻译请核对页面//经核对是门禁定时下载记录时用到的。
catalog[" 点自动从设备获取新记录"] = " o'Relógio atualizado automaticamente todo dia.";
catalog["注：请确保服务器在设置的时间点处于开机状态。"] = "Nota: Verifique se o servidor estara ligado durante o tempo que você definir.";
catalog["定时下载记录时间设置成功！该设置将在软件服务或者操作系统重启后生效！"] = "Acerto de Horário realizado com sucesso! As configurações terão efeito após reiniciar o serviço de software ou o sistema operacional";
catalog["定时下载记录事件设置失败！请重试！"] = "Acerto de Horário falhou! Por favor, tente novamente!";
catalog["请输入有效的时间点(0-23)！"] = "Por favor entre com uma hora válida(0-23)!";
catalog["无"] = "Nenhum";
catalog["请输入有效的IPv4地址！"] = "Por favor, insira um end. IPv4 válido.";
catalog["请输入有效的网关地址！"] = "Por favor, insira um end. de gateway válido.";
catalog["请输入有效的子网掩码！"] = "Por favor, insira másc. de sub-rede válida.";
catalog["获取设备扩展参数失败，当前操作不可用！"] =  "Falha na obtenção do parâmetro de extensão do equipamento atual selecionado, a operação atual está indisponível.";
catalog["请选择要关闭的辅助输出点！"] = "Favor verificar a porta auxiliar que deseja fechar.";
catalog["请选择辅助输出点！"] = "Por favor selecione o ponto de saída auxiliar.";
catalog["请输入正确的时间！"] = "Por favor digite a hora correta.";
catalog["退出"] = "Sair";
catalog["正在搜索中,请等待!"] = "Procurando. Favor aguardar!"; 
catalog["当前共搜索到的门禁控制器总数为："] = "A quantidade total de Painél de Controle de Acesso encontrada é:";
catalog["自定义设备名称"] = "Customizar o nome do equipamento";
catalog["新增时删除设备中数据"] = "Limpar dados no dispositivo quando adicionado";
catalog["设备名称不能为空，请重新添加设备！"] = "O nome do equipamento não pode estar em branco. Favor adicionar o equipamento novamente.";
catalog["的设备添加成功！"] = " equipamento foi adicionado com sucesso!";
catalog["已添加设备数："] = "quantidade de equipamentos adicionados";
catalog["IP地址："] = "Endereço de IP:";
catalog[" 已存在！"] = "já existente!";
catalog["序列号："] = "Número de série:";
catalog["IP地址为："] = "Endereço de IP:";
catalog[" 的设备添加失败！原因："] = " não conseguiu ser adicionado, a razão: ";
catalog["设备连接成功，但无数据返回，添加设备失败！"] = "Equipamento adicionado com êxito, mas não há resposta dos dados enviados, podendo indicar falha na adição do equipamento.";
catalog["设备连接失败(错误码："] = "Falha na conexão do equipamento (cód. erro: ";
catalog[")，无法添加该设备！"] = "), então não pode ser adicionado.";
catalog["设备连接失败(原因："] = "Falha na conexão do equipamento (devido a:";
catalog["修改设备IP地址"] = "Modificar End. IP do equipamento";
catalog["请输入设备通讯密码:"] = "Insira a senha de comunicação do equipamento";
catalog["新的IP地址不能为空！"] = "O novo endereço IP não pode ser em branco.";
catalog["请输入一个有效的IPv4地址！"] = "Por favor, insira um End. IPv4 válido.";
catalog["请输入一个有效的网关地址！"] = "Por favor, insira um gateway válido.";
catalog["请输入一个有效的子网掩码！"] = "Por favor, insira uma máscara de sub-rede válida.";
catalog["该IP地址的设备已存在或该IP地址已被使用，不能添加！请重新输入！"] = "Já existe um equipamento com esse End. de IP ou já está em uso, e não pode ser adicionado. Por favor, insira outro.";
catalog["设备连接成功，但修改IP地址失败！"] = "Equipamento conectado com êxito, mas ocorreu falha na modificação do end. do IP.";
catalog["设备连接失败，故修改IP地址失败！"] = "Ocorreu falha na conexão do equipamento, então o End. IP não pode ser modificado.";
catalog["没有搜索到门禁控制器！"] = "Não foi encontrado nenhum Painel de Controle de Acesso.";
catalog["没有可选的门禁权限组！"] = "Não há nível de acesso disponível.";
catalog["门禁快速上手"] = "Início Rápido do Controle de Acesso";
catalog["最近门禁异常事件"] = "Exceção Recente de Controle de Acesso";
catalog["地图宽度到达上限(1120px)，不能再放大！"] = "Atingido o limite máximo com (1120px), não é possivel aumentar!";
catalog["地图宽度到达下限(400px)，不能再缩小！"] = "Atingido o limite mínimo com (400px), não é possivel reduzir!";
catalog["地图高度到达下限(100px)，不能再缩小！"] = "Atingido o limite mínimo com (100px), não é possivel reduzir!";
catalog["门图标的位置（Top或Left）到达下限，请稍作调整后再进行缩小操作！"] = "A localização (topo ou esquerda) da porta atingiu os valores mínimos, por favor, faça alguns ajustes e então continue a estreitar o mapa!";
catalog["夏令时名称不能为空！"] = "O DLST não pode estar vazio!";


catalog["请选择人员!"] = "Por favor, selecione uma pessoa!";
catalog["考勤"] = "Marcação";
catalog["员工排班表"] = "Tabela de horário do pessoal";
catalog["临时排班表"] = "Tabela de horário temporário";
catalog["排班时间段详细明细"] = "Detalhes da agenda dos horários de turno";
catalog["排班时间段详细明细(仅显示三个月)"] = "detalhes da agenda dos horários de turno (somente 3 meses)";
catalog["排班时间段详细明细(仅显示到年底)"] = "detalhes da agenda dos horários de turno (somente para final do ano";
catalog["请选择一个班次"] = "Selecione um turno";
catalog["结束日期不能小于开始日期!"] = "A data final não pode ser anterior a data inicial!";
catalog["请输入开始日期和结束日期! "] = "Por favor, coloque a data inicial e a final.";
catalog["只能设置一个班次! "] = "Você pode configurar somente um turno.";
catalog["请选择时段"] = "Selecione o horário do turno";
catalog["选择日期"] = "Selecione a data";
catalog["第"] = "No.";
catalog["周的周期不能大于52周"] = "O período semanal não pode exceder 52 semanas.";
catalog["月的周期不能大于12个月"] = "O período mensal não pode exceder 12 meses.";
catalog["天"] = "dia";
catalog["时间段明细"] = "Detalhes dos horários dos turnos";
catalog["确定删除该时段吗？"] = "Tem certeza que deseja apagar esse horário de turno?";
catalog["操作失败 {0} : {1}"] = "falha na operação {0} : {1}";
catalog["已选择"] = "selecionado";
catalog["补签卡"] = "adicionar log";
catalog["补请假"] = "adicionar saída";
catalog["新增排班"] = "adicionar agenda";
catalog["临时排班"] = "agenda temporária";
catalog["每日考勤统计表"] = "tabela de estatística diária";
catalog["考勤明细表"] = "detalhes da marcação";
catalog["请假明细表"] = "detalhes da saída";
catalog["考勤统计汇总表"] = "sumário das estatísticas";
catalog["原始记录表"] = "Tabela de log CA";
catalog["补签卡表"] = "adicionar tabela de log";
catalog["请假汇总表"] = "sumário de saída";
catalog["考勤快速上手"] = "Início Rápido da monitoração da marcação";
catalog["本日出勤率"] = "Taxa da Marcação do Dia";
catalog["当天存在员工排班时"] = "tinha compromisso no dia corrente";


//2012.8.14 add by Darcy
catalog["服务器处理数据失败，请重试！错误码："] = "Falha no processamento de dados no servidor. Por favor, tente novamente! Código do erro:";

catalog["'满足任意一个' 值域必须是以','隔开的多个值"] = "Apenas o valor dividido com múltiplas ',' pode atender a qualquer faixa de valor '.";

catalog["确认"] = "OK";

catalog[" 已添加过波特率不为："] = " acrescentou o dispositivo não com o baudrate:";

catalog[" 的设备！同一个串口下不允许存在多个波特率不同的设备。请重新选择波特率！"] = ". Por favor, certifique-se que uma porta serial só pode existir dispositivos com a mesma taxa de transmissão e escolher a velocidade de transmissão de novo! ";

catalog["提示：设备连接成功，但获取设备扩展参数失败"] = "Dica: O dispositivo é conectado com sucesso, mas não conseguiu obter os parâmetros expandidos para o dispositivo";

catalog["，继续添加？"] = ", Continuar a acrescentar?";

catalog["一体机，继续添加？"] = "dispositivo de controle de acesso Continue a adicionar?";

catalog["添加辅助点到当前地图"] = "Adicionar para auxiliar o mapa atual";

catalog["请选择要添加的辅助点！"] = "Por favor escolha o auxiliar que você deseja adicionar!";

catalog["当前门处于常开状态，是否禁用当天常开时间段后关门？"] = "A porta atual é normal aberto agora, se deve desativar Intraday Passage Fuso Horário Mode e fechar a porta?";

catalog["当前已常开"] = "Atualmente aberta normal";




catalog["发送请求失败！"] = "Falha ao enviar o pedido!";

catalog["发送请求成功！"] = "com sucesso o envio do pedido";

catalog["发送请求失败，请重试！"] = "Falha ao enviar a solicitação por favor tente novamente!";

catalog["当前设备状态不支持该操作！"] = "status do dispositivo atual não suporta esta operação!";

catalog["该人员没有登记照片！"] = "Sem imagem.";

catalog["注：1.请确保服务器在设置的时间点处于开机状态。<br/> 2.如需设置多个时间点，请以逗号分开。"] = "Nota: 1.Please garantir que o servidor está ligado no tempo set <br/> 2 Para definir múltiplos pontos temporais, separados por vírgulas.";

catalog[" 的设备添加异常！原因："] = "dispositivo é adicionado a título excepcional, motivo:";

catalog["的设备添加成功，但设备扩展参数获取失败！原因："] = "Razão dispositivo é adicionado com sucesso, mas seu parâmetro de extensão não ser obtida:";

catalog["原IP地址"] = "Endereço IP Original";

catalog["新IP地址"] = "Endereço IP Nova";

catalog["网关地址"] = "Endereço de Gateway";

catalog["子网掩码"] = "Máscara de sub-rede"

catalog["操作失败！原因："] = "A operação falhou Motivo:";

catalog["指纹模板错误，请重新登记！"] = "Erro template da impressão digital, por favor registrar a impressão digital de novo!";

catalog["卡号"] = "Número de cartão"

catalog["产品ID"] = "Pruduct ID";

catalog["所选的部门总数不能大于2000"]="Departamentos selecionados não pode exceder 2000 total";

catalog["操作成功！"] = "A operação foi bem sucedida!";

catalog["操作失败！"] = "A operação falhou!";

catalog["服务器处理数据失败，请重试！错误码："] = "The server fails to process data. Please try again! Error code:";



catalog["重连间隔时间必须为整数！"] = "O inverval religação deve ser numérico!";

catalog["设置成功，重启服务后生效！"]= "Definir com sucesso, as configurações terão efeito após reiniciar o serviço de software ou sistema operacional!";

catalog["设置成功！"]= "Definir com sucesso!";

catalog["获取记录时间点不能为空！"] = "O tempo de obtenção de novas entradas não pode estar vazio!";

catalog["用户注册失败，请检查设备配置"] = "Falha ao registar um utilizador, por favor, verifique a configuração do dispositivo";

catalog["目前该功能仅支持IE系列及IE内核的浏览器，请更换！"] = "Esta função só pode apoiar IE seris browsers.Please mudá-lo!";

catalog["请选择视频设备！"] = "Por favor, escolha um dispositivo!";

catalog["控件初始化失败，请确定视频设备类型是否选择正确或重装控件！"] = "Falha ao inicializar ocx, certifique-se o tipo de dispositivo está correto ou reinstalar ocx!";

catalog["预览失败"] = "Falha ao visualizar";

catalog["邮箱地址格式不正确"] = "Endereço de caixa de correio inválido";

catalog["请输入邮箱地址"] = "Por favor, indique o endereço de e-mail";

catalog["邮件通知"] = "E-mail de notificação";

catalog["报警监控"] = "Monitoramento de alarmes";

catalog["辅助输入"] = "Entrada auxiliar";

catalog["辅助输出"] = "Saída auxiliar";


catalog["请输入邮箱地址"] = "Por favor, indique o endereço de e-mail";

catalog["请输入邮箱地址，多个地址用 ';' 隔开"] = "Por favor, indique o endereço de e-mail, endereço mais com ';'";

catalog["邮件发送成功!"] = "E-mail enviado com sucesso!";

catalog["邮件发送失败!"] = "Enviar e-mail falhou!";

catalog["邮件发送失败,门禁参数配置中邮箱配置错误!"] = "Enviar e-mail não, os parâmetros de controle de acesso na configuração de falha de configuração caixa de correio!";

catalog["请选择报警设备!"] = "Por favor escolha o dispositivo de alarme";

catalog["门状态"] = "Status da porta";

catalog["门锁状态"] = "Estado Door";

catalog["报警类型"] = "Tipo de alarme";

catalog["门关报警"] = "Porta fechada e Alarme";

catalog["门开报警"] = "Porta aberta e alarme";

catalog["解锁"] = "Destravado";

catalog["没有报警"] = "Nenhum";

catalog["防拆"] = "Tamper";

catalog["胁迫密码开门"] = "Senha de Coação Open";

catalog["门被意外打开"] = "Aberto à força";

catalog["请先关闭门！"] = "Por favor, feche a porta em primeiro lugar!";

catalog["胁迫开门"] = "Coação Open";

catalog["胁迫指纹开门"] = "Fingerprint Coação Open";

catalog["视频服务器登录失败，请确认后重试！原因："] = "Falha ao logar no servidor de vídeo, por favor verifique e tente novamente Motivo:";

catalog["视频服务器登录失败，请确认后重试！错误码："] = "Falha ao logar no servidor de vídeo, por favor verifique e tente novamente Código de erro:";

catalog["视频回放失败，请确认后重试！原因："] = "Falha ao reproduzir o vídeo, por favor verifique e tente novamente Motivo:";


catalog["视频回放失败，请确认后重试！错误码："] = "Falha ao reproduzir o vídeo, por favor verifique e tente novamente Código de erro:";

catalog["视频服务器登录失败，请确认后重试！"] = "Falha ao logar no servidor de vídeo, por favor verifique e tente novamente!"

catalog["当前系统中没有添加视频服务器，请添加！"] = "O sistema tem nenhum vídeo server.Please adicionar primeiro!";

catalog["视频通道不能重复选择，请重新选择！"] = "O canal de vídeo não pode ser repetido seleção, selecione novamente!";

catalog["读头"] = "Leitor";

catalog["名称"] = "Nome";

catalog["视频时长不能小于0，请输入正确的视频时长!"] = "O intervalo de exibição de vídeo não pode ser inferior a 0s, digite o correto!";

catalog["录像时长不能小于0，请输入正确的录像时长!"] = "O intervalo de gravação de vídeo não pode ser inferior a 0s, digite o correto!";

catalog["添加摄像机到当前地图"] = "Adicionar câmeras para o mapa atual";

catalog["请选择要添加的摄像头！"] = "Por favor, escolha as câmeras que você deseja adicionar!";

catalog["视频查询"] = "Video Search"

catalog["视频联动"] = "Video Linkage";

catalog["视频加载中，请稍侯......"] = "Carregamento do vídeo, por favor aguarde...";

catalog["该通道已达最大访问量或视频服务器未连接!"] = "O canal atingiu o seu máximo de tráfego ou servidor de vídeo não está conectado!";

catalog["预览失败，请确认后重试！原因："] = "Preview falhar, certifique-se e tente novamente Razões:";

catalog["预览失败，请确认后重试！错误码："] = "Preview falhar, certifique-se e tente novamente Código de erro:";

catalog["无此权限！"] = "Sem essa permissão!";

catalog["没有录像文件！"] = "Nenhum arquivo de vídeo";

catalog["该通道已达最大访问量或视频服务器未连接！"] = "O canal atingiu o seu máximo de tráfego ou servidor de vídeo não está conectado!";

catalog["从视频服务器导出失败！"] = "Exportar falha do servidor de vídeo";

catalog["从视频服务器导出成功！"] = "O sucesso das exportações a partir do servidor de vídeo";

catalog["视频弹出窗口高度必须为整数！"] = "Video altura da janela pop-up deve ser um inteiro!";

catalog["请选择需要设置的对象!"] = "Selecione o objeto que você precisa configurar!";

catalog["请启用当前视频设备下被禁用的视频通道！"] = "Por favor habilite canal de vídeo do equipamento de vídeo atual!";

catalog["HIKVISION_ERROR_1"] = "Usuário ou senha incorreta.";

catalog["HIKVISION_ERROR_4"] = "Não. canal errado.";

catalog["HIKVISION_ERROR_5"] = "Exceder o número máximo de cliente para se conectar ao DVR.";

catalog["HIKVISION_ERROR_7"] = "Falha ao conectar o DVR.";

catalog["HIKVISION_ERROR_8"] = "Falha ao enviar dados para DVR.";

catalog["HIKVISION_ERROR_10"] = "Timeout ao obter dados de DVR.";

catalog["HIKVISION_ERROR_17"] = "parâmetro errado.";

catalog["HIKVISION_ERROR_19"] = "Nenhum disco rígido.";

catalog["HIKVISION_ERROR_20"] = "erro de disco rígido.";

catalog["HIKVISION_ERROR_21"] = "Servidor de disco rígido está cheio.";

catalog["HIKVISION_ERROR_22"] = "Servidor erro no disco rígido.";

catalog["HIKVISION_ERROR_24"] = "Servidor ocupado.";

catalog["HIKVISION_ERROR_28"] = "Falta de recursos de DVR.";

catalog["HIKVISION_ERROR_29"] = "Operação DVR falhou.";

catalog["HIKVISION_ERROR_33"] = "O servidor não tem o arquivo especificado durante a reprodução.";

catalog["HIKVISION_ERROR_36"] = "A última operação ainda não está completa.";

catalog["HIKVISION_ERROR_38"] = "Erro de reprodução.";

catalog["HIKVISION_ERROR_46"] = "O número de máximo.";

catalog["HIKVISION_ERROR_47"] = "Usuário não existe.";

catalog["HIKVISION_ERROR_52"] = "O maior número de usuários.";

catalog["HIKVISION_ERROR_74"] = "ID do usuário no cancelamento de passar por uma cirurgia.";

catalog["HIKVISION_ERROR_90"] = "O dispositivo que está sendo feito o backup.";

catalog["许可信息"] = "Licença Standard Version";

catalog["请切换为英文输入法状态！"] = "Por favor, mude para o estado Inglês método de entrada!";

catalog["许可信息"] = "Informações sobre a licença";

catalog["请选择每个扩展板的继电器数量！"] = "Por favor seleccione a contagem de relés para cada placa estendida!";

//登录页面验证
catalog["比对验证中，请稍等!"] = "Do que na verificação, por favor, espere!";
catalog["验证失败，请重试!"] = "Validação falhou, por favor tente novamente!";
catalog["10.0指纹算法许可失败!"] = "10.0 licença algoritmo de impressão digital falhou!";
catalog["验证通过，登录系统!"] = "Verifique se por, fazer logon no sistema!";
catalog["获取指纹失败，请重试!"] = "Obter impressão digital falhou, por favor tente novamente!";
catalog["登记指纹功能只支持IE浏览器"] = "A função de impressão digital registrada só suporta navegador IE";
catalog["请安装指纹仪驱动"] = "Por favor, instale o driver de dispositivo de impressão digital";

//访客
catalog["进入地点"] = "Introduza A Localização";
catalog["离开地点"] = "Deixe O Local";
catalog["被访人姓名"] = "Nome Entrevistados";
catalog["被访人姓氏"] = "Sobrenome Entrevistados";
catalog["是否重新打印访客单？"] = "Visitantes se reimpressão único?";
catalog["没有注册读写器控件，是否下载控件？"] = "Não é cadastrado controle leitor se quer baixar controles?";
catalog["没有注册扫描仪控件，是否下载控件？"] = "Não tem um controle do scanner registrado, se quer baixar controles?";
catalog["没有注册读写器控件，是否下载控件？"] = "Não é cadastrado controle leitor se quer baixar controles?";
catalog["暂时不支持该证件类型！"] = "Temporariamente não suporta o tipo de documento!";
catalog["请选择正确的证件类型或调整证件的位置！"] = "Por favor, selecione o tipo de documento correto ou documentos de ajuste localização!";
catalog["加载核心失败！"] = "Carregado falha núcleo!";
catalog["初始化失败！"] = "Falha na inicialização!";
catalog["请放好身份证！"] = "Por favor, coloque fora o seu ID!";
catalog["没有检测到身份证阅读器！"] = "Leitor de cartão ID não é detectado!";
catalog["目前该功能仅支持二代身份证！"] = "Este recurso só é suporte para a placa de segunda geração ID!";
catalog["没有可选的权限组！"] = "Nenhum grupo permissões opcional!";
catalog["卡号已存在，如果确认将重新发卡，请先清除该卡原持卡人"] = "The card number already exists. If you want to re-issue a card, first remove the original holder of the card ";

//init_base_frame.js
catalog["正式版许可"] = "A versão oficial de licença";
catalog["试用版许可"] = "A licença de avaliação";

catalog["断开"] = "Desconectado";
catalog["短路"] = "Curto";

//Employee_edit.html
catalog["没有可选的梯控权限组！"] = "Sem o opcional de Elevador Nível!";

//Dev_RTMonitor.html
catalog["请先停止监控再导出！"] = "Por favor, pare de monitoramento antes da exportação!";
catalog["服务未启动"] = "Serviço não Correndo";
catalog["门禁服务未启动，请先点击左方启动服务按钮"]= "Serviço de acesso não for iniciado, clique no botão 'Start Service' esquerda";

