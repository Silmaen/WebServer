<?PHP

require_once("fonctions_bd.php");

function draw_colone_gauche_timeline(){
	echo "					<ul id=\"ls_type\">\n";
	echo "						<li><a href=\"javascript:centerTimeline(-7939);\">Age 0</a></li>\n";
	echo "						<li><a href=\"javascript:centerTimeline(-6182);\">Age I</a></li>\n";
	echo "						<li><a href=\"javascript:centerTimeline(-2596);\">Age II</a></li>\n";
	echo "						<li><a href=\"javascript:centerTimeline(517);\">Age III</a></li>\n";
	echo "						<li><a href=\"javascript:centerTimeline(2007);\">Age IV</a></li>\n";
	echo "					</ul>\n";
}

function draw_colone_droite_timeline(){
	
}

function draw_colone_centre_timeline(){
	echo "<div id=\"t1\" class=\"timeline-default\" style=\"height: 450px; border: 1px solid #aaa\">\n";
	echo "</div>\n";
	echo "<noscript>\n";
	echo "	This page uses Javascript to show you a Timeline. Please enable Javascript in your browser to see the full page. Thank you.\n";
	echo "</noscript>\n";
}

?>
