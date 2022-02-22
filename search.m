close all;
clear all;
clc;

%% 21 February 2022
[s, Fs] = audioread('./shared_local/RAD_BEDOUR_20220211_1740_BEDINA_SYS001.wav');
fprintf('%d', Fs);
specgram(s, 1024, Fs);
