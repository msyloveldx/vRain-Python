#!/usr/bin/perl
#0、[!]务必首先手动备份text到text_ba目录，避免原始文本修改或丢失
#1、fontcheck.pl : 检查text_ba目录下所选文本字符的主字体支持情况，把主字体不支持的字符及频次写入replace.tmp文件
#2、replaces.txt : 编辑replace.tmp文件，按最小化原则按需更新频次较高、字形标准不同的字符，手工另存为.txt文件，用于改善字体的支持情况
#3、replace.pl   : 读取text_ba目录下的文件，根据replace.txt替换字符并覆盖写入text目录对应文件
#4、回主目录运行vrain.pl重新制作书籍
#by shanleiguang@gmail.com, 2025
use strict;
use warnings;

use Font::FreeType;
use Getopt::Std;
use Encode;
use utf8;

binmode(STDIN, ':encoding(utf8)');
binmode(STDOUT, ':encoding(utf8)');
binmode(STDERR, ':encoding(utf8)');

#读取书籍配置文件
my %book;
open BCONFIG, "< book.cfg";
print "read 'book.cfg'...\n";
while(<BCONFIG>) {
	chomp;
	next if(m/^\s{0,}$/);
	next if(m/^#/);
	s/#.*$// if(not m/=#/);
	s/\s//g;
	my ($k, $v) = split /=/, $_;
	$v = decode('utf-8', $v);
	$book{$k} = $v;
}
close(BCONFIG);
print "\t标题：$book{'title'}\n";
print "\t作者：$book{'author'}\n";
print "\t背景：$book{'canvas_id'}\n";
print "\t字体1：$book{'font1'}\n";
print "\t字体2：$book{'font2'}\n";
print "\t字体3：$book{'font3'}\n";
print "\t字体4：$book{'font4'}\n";

my ($fn1, $fn2, $fn3, $fn4) = ($book{'font1'}, $book{'font2'}, $book{'font3'}, $book{'font4'});
my %opts;

getopts('f:t:', \%opts);

my $from = $opts{'f'} ? $opts{'f'} : 1;
my $to = $opts{'t'} ? $opts{'t'} : 1;
my %rchars; #保存字体font1不支持的字符

opendir TBADIR, 'text_ba';
foreach my $tfn (sort readdir(TBADIR)) {
	next if($tfn !~ m/\.txt$/i);
	my ($content, @chars);
	print "checking 'text_ba/$tfn' ... \n";
	open TEXTBA, "< text_ba/$tfn";
	{ local $/ = undef; $content = <TEXTBA>; }
	close(TEXTBA);
	$content = decode('utf-8', $content);
	$content =~ s/\|//g;
	@chars = split //, $content;
	foreach my $cid (0..$#chars) {
		my $char = $chars[$cid];
		if(not $rchars{$char}) {
			my $fn = get_font($char, [$fn1, $fn2, $fn3, $fn4]);
			if(defined $fn and $fn ne $fn1) {
				$rchars{$char}{'font'} = $fn;
				$rchars{$char}{'count'} = 1;
			}
		} else {
			$rchars{$char}{'count'}++;
		}
	}
}
close(TBADIR);

open RTMP, '> replace.tmp';
foreach my $rc (sort {$rchars{$b}{'count'}<=>$rchars{$a}{'count'}} keys %rchars) {
	print RTMP "$rc|$rchars{$rc}{'font'}|$rchars{$rc}{'count'}|\n";
}
close(RTMP);

sub get_font {
	my ($char, $fref) = @_;
	my @fonts = @$fref;
	foreach my $f (@fonts) {
		return $f if(font_check($f, $char));
	}
	return undef;
}

sub font_check {
	my ($font, $char) = @_;
	$font = "../../fonts/$font";
	my $freetype = Font::FreeType->new();
	my $face = $freetype->face($font);
	my $fontglyph = $face->glyph_from_char($char);

	return 1 if($fontglyph);
	return 0;
}
