from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime
from dateutil.relativedelta import relativedelta


class PamCodeIso(models.Model):
    _name = 'pam.code.iso'

    name = fields.Selection([
        ('rekap_jurnal', 'Rekapitulasi Jurnal'),
        ('verifikasi_jurnal', 'Verifikasi Jurnal'),
        ('rekap_buku_besar', 'Rekap Buku Besar'),
        ('laporan_buku_besar', 'Laporan Buku Besar'),
        ('neraca', 'Neraca'),
        ('laba_rugi', 'Laba Rugi'),
        ('r_k_s', 'Ringkasan Kegiatan Utama'),
        ('sak_etap', 'SAK ETAP'),
        ('perincian_biaya', 'Laporan Perincian Biaya'),
        ('aspek_keuangan', 'Laporan Aspek Keuangan'),
        ('arus_kas', 'Laporan Arus Kas'),
        ('perputaran_kas', 'Laporan Perputaran Kas'),
        ('jurnal_pembayaran_kas', 'Daftar Jurnal Pembayaran Kas'),
        ('dph', 'Daftar Pengeluaran Harian'),
        ('dhhd_terbuka', 'DHHD Terbuka'),
        ('dhhd_terbuka_detail', 'Detail DHHD Terbuka'),
        ('aset_tetap', 'Laporan Aset Tetap'),
        ('laporan_penyusutan', 'Laporan Penyusutan')
    ], default='rekap_jurnal', required=True)
    code_iso = fields.Text(string='Kode ISO', required=True)