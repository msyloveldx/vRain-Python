#!/usr/bin/perl
#压缩某一目录下的文件名不是以'_已压缩'结尾的PDF文件，如'perl pdfcompress ../pdf'
#by shanleiguang, 2025.4
use strict;
use warnings;

use Getopt::Std;
use Encode;
use utf8;

binmode(STDIN, ':encoding(utf8)');
binmode(STDOUT, ':encoding(utf8)');
binmode(STDERR, ':encoding(utf8)');

my %opts;

getopts('d:', \%opts);

if(not $opts{'d'} and not -f $opts{'d'}) {
	print "错误：未定义'-d'目标目录或目标目录不存在！";
	exit;
}

my $dir = $opts{'d'};

opendir PDFDIR, $dir;
foreach my $f (readdir(PDFDIR)) {
	$f = decode('utf-8', $f);
	next if($f !~ /\.pdf$/i);
	next if($f =~ /_已压缩\.pdf$/i);
	my $fn = (split /\./, $f)[0];
	my $input = "$dir/$f";
	my $output = "$dir/$fn".'_已压缩.pdf';
	
	print "压缩PDF文件'$output'...";
	`gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen -dNOPAUSE -dQUIET -dBATCH -sOutputFile=$output $input`;
	`rm $input`;
	print "完成！\n";
}
closedir(PDFDIR);