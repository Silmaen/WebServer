<?PHP

function connexion_bd(){
	$dbhost='127.0.0.1';
	$dbusername="siteapache";
	$dbuserpass="totocaca";
	$dbname='ayoaron';
	//connexion au serveur
	$link_id = mysqli_connect ($dbhost, $dbusername, $dbuserpass, $dbname);
	if (mysqli_connect_errno()){
		echo "problème de connexion serveur MySQL '$dbname@$dbhost' : ",mysqli_connect_error(),"<br>\n";
		exit();
	}
	mysqli_query($link_id,"SET NAMES 'utf8'");
	return $link_id;
}

?>