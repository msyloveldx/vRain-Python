#!/usr/bin/perl
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
open BCONFIG, "< books/$book_id/book.cfg";
print "读取书籍排版配置文件'books/$book_id/book.cfg'...\n";
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
print "\t标题：$book{'title'}\n";
print "\t作者：$book{'author'}\n";
print "\t背景：$book{'canvas_id'}\n";
print "\t每列字数：$book{'row_num'}\n";
print "\t是否无标点：$book{'if_nocomma'}\n";
print "\t标点归一化：$book{'if_onlyperiod'}\n";
close(BCONFIG);

my ($fn1, $fn2, $fn3, $fn4) = ($book{'font1'}, $book{'font2'}, $book{'font3'}, $book{'font4'});
my %opts;

getopts('f:t:', \%opts);

my $from = $opts{'f'} ? $opts{'f'} : 1;
my $to = $opts{'t'} ? $opts{'t'} : 1;
my %rchars; #保存替换字符

open RTXT, '< replace.txt';
while(<RTXT>) {
	chomp;
	$_ = decode('utf-8', $_);
	my @tmp = split /\|/, $_;
	if($tmp[3]) {
		my $fnr = get_font($tmp[3], [$fn1, $fn2, $fn3, $fn4]); #替换后字符的字体
		if($fnr eq $fn1 or $fnr eq $fn2) { #替换后字符的字体等于fn1、fn2时，才进行替换
			$rchars{$tmp[0]} = $tmp[3];
		}
	}
}
close(RTXT);

opendir TBADIR, "text_ba";
foreach my $tfn (sort readdir(TBADIR)) {
	next if($tfn !~ m/\.txt$/i);
	my ($content, @chars);
	print "replacing 'text_ba/$tfn' ... \n";
	open TEXTBA, "< text_ba/$tfn";
	{ local $/ = undef; $content = <TEXTBA>; }
	close(TEXTBA);
	$content = decode('utf-8', $content);
	foreach my $from (keys %rchars) {
		my $to = $rchars{$from};
		$content =~ s/$from/$to/g;
	}
	open TEXT, "> text/$tfn";
	print TEXT $content;
	close(TEXT);
}
close(TBADIR);

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
	my $freetype = Font::FreeType->new();
	my $face = $freetype->face("fonts/$font");
	my $fontglyph = $face->glyph_from_char($char);

	return 1 if($fontglyph);
	return 0;
}
