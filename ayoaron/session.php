<?PHP
date_default_timezone_set("CET");
session_start();

if ($_POST['envoi']=="logout" ) {
	session_unset();
	session_destroy();
} else if ($_POST['envoi']=="connexion") {
	$dbhost='127.0.0.1';
	$dbusername="siteapache";;
	$dbuserpass="totocaca";
	$dbname='adiministration';
	//connexion au serveur
	$link_id = mysqli_connect ($dbhost, $dbusername, $dbuserpass, $dbname);
	//connexion à la base
	if (mysqli_connect_errno) die(mysqli_connect_error());
	$requette="SELECT * FROM `users` WHERE login='".$_POST['login']."'";
	$result =  mysqli_query($link_id,$requette);
	if ($result) {
		$row = mysqli_fetch_row($result);
		if (md5($_POST['pasword'])==$row[2]){
			$_SESSION['acces']="oui";
			//on a un utilisateur enregistrer
			$_SESSION['ID']=$row[0];
			$_SESSION['nom']=$row[3];
			$_SESSION['login']=$row[1];
			$_SESSION['acred']=$row[5];
			$_SESSION['email']=$row[4];
		} else {
			echo "Login incorrect!<br>";
		}
	}else{
		echo "requette: ",$requette,"<br>";
		echo "réponse: ",$result,"<br>";
		echo "database: ",$dbname,"<br>";
	}
	mysqli_close($link_id);
}
$_POST['envoi']=="" ;
?>