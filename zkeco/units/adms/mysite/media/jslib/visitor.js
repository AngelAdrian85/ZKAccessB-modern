//入口
function init_param(reader_id, scan_id)
{
	var $reader = $("#"+reader_id);//二代证读写器
	var $scan = $("#"+scan_id);//扫描仪
	
	$reader.click(function(){
		alert("读写器");
	});
	
	$scan.click(function(){
		alert("扫描仪");
	});
	
}

//摄像头拍照功能-darcy20120322
function myFlash_DoFSCommand(command, args){
    if(command === "send_pic")//发送的是base64的图片
    {
		var photo_byte = "data:image/gif;base64,"+args;
		return photo_byte;
    }
}

// 打印访客单
function print_form()
{
	$("#id_print_button").remove();
    PrintActiveX.paddingTop=30;
    PrintActiveX.paddingRight=0;
    PrintActiveX.paddingBottom=0;
    PrintActiveX.paddingLeft=50;
    PrintActiveX.header="<div style=\"float:left;border-bottom:1px solid #eeeeee;padding:0px;\">&b&w<span style=\"padding-right:20px;float:right\"></span>&b</div>";
    PrintActiveX.footer="<div style=\"float:left;border-bottom:1px solid #eeeeee;padding:0px;\">&b&w<span style=\"padding-right:20px;float:right\"></span>&b</div>";
    PrintActiveX.pageWidth=800;// 纸张宽度
    PrintActiveX.pageHeight=1250;// 纸张高度
    PrintActiveX.orientation=1;// 0 横向打印，1 纵向打印
	//PrintActiveX.PrintView();// 打印预览
	PrintActiveX.Print(false);// 直接打印
	
	window.setTimeout(function(){
		top.$.jBox.close('visitorFormBox');// 需要延时关闭，否则访客单会出现问题
	}, 1000);
}
