-- Journal JU
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '11111120' limit 1) WHERE id = 428;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '11111120' limit 1) WHERE id = 450;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '4266B110' limit 1) WHERE id = 1340;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '42711140' limit 1) WHERE id = 1456;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '41311130' limit 1) WHERE id = 1463;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '42711120' limit 1) WHERE id = 1470;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '41311180' limit 1) WHERE id = 1472;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '41211220' limit 1) WHERE id = 1478;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '41111190' limit 1) WHERE id = 1507;

-- Journal AP
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21151120' limit 1) WHERE id = 1912;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 1850;

-- Journal CO
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 1964;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2287;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2305;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2315;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2326;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2328;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2352;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2382;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2388;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2402;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2438;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2442;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2452;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2462;
UPDATE pam_journal_entry_line SET debit = 120711800 WHERE id = 2470;
INSERT INTO pam_journal_entry_line(journal_entry_id, coa_id, debit, credit, create_uid, create_date, write_uid, write_date) VALUES (715, (select id from pam_coa where code = '21111110' limit 1), 140868200, 0, 1, NOW(), 1, NOW());
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2482;
UPDATE pam_journal_entry_line SET debit = 11055000 WHERE id = 2486;
INSERT INTO pam_journal_entry_line(journal_entry_id, coa_id, debit, credit, create_uid, create_date, write_uid, write_date) VALUES (723, (select id from pam_coa where code = '21111110' limit 1), 54295000, 0, 1, NOW(), 1, NOW());
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2488;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2538;
INSERT INTO pam_journal_entry_line(journal_entry_id, coa_id, debit, credit, create_uid, create_date, write_uid, write_date) VALUES (754, (select id from pam_coa where code = '21111110' limit 1), 258564400, 0, 1, NOW(), 1, NOW());
UPDATE pam_journal_entry_line SET debit = 33652800 WHERE id = 2548;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2590;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2592;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2598;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2606;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2646;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2648;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2650;
UPDATE pam_journal_entry_line SET debit = 303557550 WHERE id = 2652;
INSERT INTO pam_journal_entry_line(journal_entry_id, coa_id, debit, credit, create_uid, create_date, write_uid, write_date) VALUES (806, (select id from pam_coa where code = '21111110' limit 1), 132159450, 0, 1, NOW(), 1, NOW());
INSERT INTO pam_journal_entry_line(journal_entry_id, coa_id, debit, credit, create_uid, create_date, write_uid, write_date) VALUES (823, (select id from pam_coa where code = '21111110' limit 1), 85004700, 0, 1, NOW(), 1, NOW());
UPDATE pam_journal_entry_line SET debit = 15084300 WHERE id = 2687;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2701;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2715;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 2717;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2410;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2412;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2416;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2492;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2494;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2496;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2500;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2502;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2550;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2552;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2554;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2556;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2558;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2560;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2562;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2564;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2566;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2588;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2624;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2610;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2626;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2628;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2662;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2675;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2677;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2685;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21121110' limit 1) WHERE id = 2697;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '21111110' limit 1) WHERE id = 1944;

-- Journal CI
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '11112190' limit 1) WHERE id = 1;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '11112140' limit 1) WHERE id = 603;

-- Journal BL
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '11132120' limit 1) WHERE id = 75;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '11132120' limit 1) WHERE id = 928;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '31111160' limit 1) WHERE id = 1198;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '31121180' limit 1) WHERE id = 37;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '11132110' limit 1) WHERE id = 83;

-- Journal IN
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '11161110' limit 1) WHERE id = 33;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '41214110' limit 1) WHERE id = 32;
UPDATE pam_journal_entry_line SET coa_id = (select id from pam_coa where code = '41321110' limit 1) WHERE id = 125;
