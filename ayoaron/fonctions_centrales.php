<?PHP


require("fonctions_news.php");
require("fonctions_histoire.php");
require("fonctions_timeline.php");
require("fonctions_developpement.php");
require("fonctions_langue.php");
require("fonctions_univers.php");

function draw_colonne_gauche($page){
	if ($page=="news")
		draw_colone_gauche_news();
	if ($page=="histoire")
		draw_colone_gauche_histoire();
	if ($page=="langue")
		draw_colone_gauche_langue();
	if ($page=="developpements")
		draw_colone_gauche_devel();
	if ($page=="univers")
		draw_colone_gauche_univers();
	if ($page=="timeline")
		draw_colone_gauche_timeline();
}

function draw_colonne_centrale($page){
	if ($page=="news")
		draw_colone_centre_news();
	if ($page=="histoire")
		draw_colone_centre_histoire();
	if ($page=="langue")
		draw_colone_centre_langue();
	if ($page=="developpements")
		draw_colone_centre_devel();
	if ($page=="univers")
		draw_colone_centre_univers();
	
	if ($page=="timeline")
		draw_colone_centre_timeline();
}

function draw_colonne_droite($page){
	if ($page=="news")
		draw_colone_droite_news();
	if ($page=="histoire")
		draw_colone_droite_histoire();
	if ($page=="langue")
		draw_colone_droite_langue();
	if ($page=="developpements")
		draw_colone_droite_devel();
	if ($page=="univers")
		draw_colone_droite_univers();
	if ($page=="timeline")
		draw_colone_droite_timeline();
}


?>