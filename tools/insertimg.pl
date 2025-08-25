#!/usr/bin/perl
#by shanleiguang, 2024.1.5
use strict;
use warnings;

use PDF::Builder;
use Getopt::Std;
use Encode;
use utf8;

binmode(STDIN, ':encoding(utf8)');
binmode(STDOUT, ':encoding(utf8)');
binmode(STDERR, ':encoding(utf8)');

my %opts;

getopts('i:', \%opts);

my $pdfn = $opts{'i'};

$pdfn = decode('utf-8', $pdfn);
if(not -f "$pdfn.pdf") { print "error: pdf file not found\n"; }

my %book;
open BCONFIG, "< book.cfg";
print "read 'book.cfg'...\n";
while(<BCONFIG>) {
	chomp;
	next if(m/^\s{0,}$/);
	next if(m/^#/);
	s/\s//g;
	s/#.*$// if(not m/=#/);
	my ($k, $v) = split /=/, $_;
	$v = decode('utf-8', $v);
	$book{$k} = $v;
}
close(BCONFIG);

my ($canvas_id, $row_num) = ($book{'canvas_id'}, $book{'row_num'});

my %canvas;
open CCONFIG, "< ../../canvas/$canvas_id.cfg";
print "read '../../canvas/$canvas_id.cfg'...\n";
while(<CCONFIG>) {
	chomp;
	next if(m/^\s{0,}$/);
	next if(m/^#/);
	s/\s//g;
	s/#.*$// if(not m/=#/);
	my ($k, $v) = split /=/, $_;
	$v = decode('utf-8', $v);
	$canvas{$k} = $v;
}
close(CCONFIG);

my ($bg_width, $bg_height) = ($canvas{'canvas_width'}, $canvas{'canvas_height'});
my ($bg_top, $bg_bottom) = ($canvas{'margins_top'}, $canvas{'margins_bottom'});
my ($bg_left, $bg_right) = ($canvas{'margins_left'}, $canvas{'margins_right'});
my ($col_num, $lc_width) = ($canvas{'leaf_col'}, $canvas{'leaf_center_width'});
my ($il_width, $ol_width, $ot_vmargin) = ($canvas{'inline_width'}, $canvas{'outline_width'}, $canvas{'outline_vmargin'});
my $cw = ($bg_width - $bg_left - $bg_right - $lc_width)/$col_num;
my $rh = ($bg_height - $bg_top - $bg_bottom)/$row_num;

my @images;
open IMGCFG, "< images.cfg";
print "read 'images.cfg'...\n";
while(<IMGCFG>) {
	chomp;
	next if(m/^\s{0,}$/);
	next if(m/^#/);
	s/\s//g;
	my ($pid, $col_begin, $col_end, $img_id) = split /\|/, $_;
	push @images, [$pid, $col_begin, $col_end, $img_id];
	print "$bg_width x $bg_height, $pid, $col_begin, $col_end, $img_id\n";
}
close(IMGCFG);

print "open pdf '$pdfn.pdf' ... \n";

my $vpdf = PDF::Builder->open("$pdfn.pdf");

foreach my $i (@images) {
	insert_img(@$i);
}

$vpdf->save($pdfn.'_image.pdf');

sub insert_img {
	my ($pid, $col_begin, $col_end, $img_id) = @_;
	my $iw = ($col_end-$col_begin+1)*$cw;
	my $ix = $bg_width-$bg_right-$cw*$col_end;

	$ix-= $lc_width if($col_begin > $col_num/2);

	my $iy = $bg_bottom;
	my $page = $vpdf->open_page($pid);
	my $grfx = $page->gfx();
	my $img1 = $vpdf->image("images/001.jpg");
	my $img2 = $vpdf->image("images/$img_id.jpg");

	$grfx->linewidth(1);
	$grfx->strokecolor('white');
	$grfx->fillcolor('white');
	$grfx->move($ix, $iy);
	$grfx->rect($ix+10, $iy+1, $iw-20, $bg_height-$bg_top-$bg_bottom-3);
	$grfx->fillstroke();
	$grfx->object($img2, $ix+10, $iy+10, $iw-20, $bg_height-$bg_top-$bg_bottom-20);
}

