function GoHref(element)
{
	location.href=element.href;
}
$(document).ready(function(){
	$('.dropdown-toggle').on('click', function(){
		GoHref(this);
	});
});