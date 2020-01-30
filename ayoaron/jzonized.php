<?php
header('Content-Type: application/json; charset=utf-8');
/* 
 * @Purpose: This file is about making JSON data
 * @author : goldsky
 * @date   : 20100210
 */
// Database settings (localhost? username? password?)
include_once('dbconfig.inc.php');

$conn = mysqli_connect($database_server, $database_user, $database_password, $dbase);
if (mysqli_connect_errno()) {
	die( "problème de connexion serveur MySQL '$dbase@$database_server' : /\\".mysqli_connect_error()."/\\");
}
mysqli_query($conn,"SET NAMES 'utf8'");

// generating event attributes inside a function
function eventAtt() {
	$dbtable			= "bd_tl_evenemrnt";
	$maquerry = "SELECT * FROM $dbtable";
	$eventQuery=mysqli_query($conn,$maquerry)  or die ("problème de connexion à la dbtable '$dbtable' : /\\".mysqli_error($idcom)."/\\");
	date_default_timezone_set('UTC');
	while ($row = mysqli_fetch_array($eventQuery)) {
		$durationEvent=FALSE;
		if ($row['duree']){
			$durationEvent=TRUE;
		}
		if ($row['fin_anticipe']== NULL || $row['fin_anticipe'] == '' || $durationEvent==FALSE){
			$ddebut = NULL;
		}else{
			$ddebut=$row['fin_anticipe'];
		}
		// ------------ optionally with "end" date ------------
		if ($row['fin']== NULL || $row['fin'] == '') {
			$enddate = NULL;     // to skip latestStart date
			$lenddate = NULL;
		}else {
			$enddate = $row['fin'];
			if ($row['fin_anticipe']== NULL || $row['fin_anticipe'] == '' || $durationEvent==FALSE){
				$lenddate = NULL;
			}else{
				$lenddate=$row['fin_anticipe'];
			}
		}
		if ($row['lien']== NULL || $row['lien'] == ''){
			$link = NULL;
		}else{
			$link = $row['lien'];
		}
		if ($row['image']== NULL || $row['image'] == ''){
			$image = NULL;
		}else{
			$image = $row['image'];
		}
		$color = NULL;
		$icon = NULL;
		$tapeImage = NULL;
		if ($row['type_evenement']== "guerre"){
			$color = "#FF0000";
			$icon = "api/js/images/epee.gif";
			$tapeImage = NULL;
		}
		if ($row['type_evenement']== "magie"){
			$color = "#0005FA";
			$icon = "api/js/images/book.gif";
			$tapeImage = NULL;
		}
		if ($row['type_evenement']== "politique"){
			$color = "#28255A";
			$icon = "api/js/images/carte.gif";
			$tapeImage = NULL;
		}
		if ($row['type_evenement']== "personnage"){
			$color = "#00AF00";
			$icon = "api/js/images/visage.gif";
			$tapeImage = NULL;
		}
		if ($row['type_evenement']== "clef"){
			$color = "#AFAF00";
			$icon = "api/js/images/lantern.gif";
			$tapeImage = NULL;
		}
		if ($row['type_evenement']== "science"){
			$color = "#AF00AF";
			$icon = "api/js/images/book.gif";
			$tapeImage = NULL;
		}
		// ------------ create the array here ------------
		$eventAtts[] = array (
				'start' => $row['debut'],
				'end' => $enddate,
				'latestStart' => $ddebut,
				'earliestEnd' => $lenddate,
				'durationEvent' => $durationEvent,
				'description' => $row['Description'],
				'caption' => $row['caption'],
				'link' => $link,
				'title' => $row['titre'],
				'image' => $image,
				'color' => $color,
				'icon' => $icon,
				'tapeImage' => $tapeImage
		);
	}
	mysqli_free_result($eventQuery);
	return $eventAtts;
}
////////////////////////////////////////////
//                                        //
//          TIMELINE'S JSON DATA          //
//                                        //
////////////////////////////////////////////
//
$json_data = array (
        //Timeline attributes
        'wiki-url'=>'http://www.argawaen.net/ayoaron',
        'wiki-section'=>'Ayoaron Timeline',
        'dateTimeFormat'=>'Ayoaron', //JSON!
        //Event attributes
        'events'=> eventAtt() // <---- here is the event arrays from function above.
);
$json_encoded=json_encode($json_data);
echo $json_encoded;
?>
