<?php
 
if(function_exists('posix_geteuid')){
    // use posix to get current uid and gid
    $uid   = posix_geteuid();
    $usr   = posix_getpwuid($uid);
    $user  = $usr['name'];
    $gid   = posix_getegid();
    $grp   = posix_getgrgid($gid);
    $group = $grp['name'];
}else{
    // try to create a file and read it's ids
    $tmp = tempnam ('/tmp', 'check');
    $uid = fileowner($tmp);
    $gid = filegroup($tmp);
 
    // try to run ls on it
    $out = `ls -l $tmp`;
    $lst = explode(' ',$out);
    $user  = $lst[2];
    $group = $lst[3];
    unlink($tmp);
}
 
echo "Your PHP process seems to run with the UID $uid ($user) and the GID $gid ($group)\n"; ?>
