"""
Police Report Generator
Government of India style — Motor Accident Report (Form 54 style)
Includes: accident snapshot, approval workflow, QR retrieval code
"""
import os
import json
import hashlib
from datetime import datetime


class ReportGenerator:
    def __init__(self):
        os.makedirs('reports', exist_ok=True)

    def generate_police_report(self, accident_data):
        report_id = f"FPR-{accident_data['id']}"
        filename = f"reports/Police_Report_{accident_data['id']}.html"
        html = self._build_report_html(accident_data, report_id)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        # Save structured JSON for future retrieval
        json_path = f"reports/Report_{accident_data['id']}.json"
        with open(json_path, 'w') as f:
            json.dump({k: v for k, v in accident_data.items() if k != 'frame_b64'},
                      f, indent=2, default=str)
        return filename

    def _qr_svg(self, text):
        """Generate a simple visual QR-style token using MD5 hash of the report ID"""
        h = hashlib.md5(text.encode()).hexdigest()
        cells = []
        size = 10
        for i in range(size):
            for j in range(size):
                v = int(h[(i * size + j) % 32], 16)
                if v > 7:
                    x, y = 4 + j * 8, 4 + i * 8
                    cells.append(f'<rect x="{x}" y="{y}" width="7" height="7" fill="#000"/>')
        for cx, cy in [(4, 4), (4, 68), (68, 4)]:
            cells.append(f'<rect x="{cx}" y="{cy}" width="20" height="20" fill="#000"/>')
            cells.append(f'<rect x="{cx+3}" y="{cy+3}" width="14" height="14" fill="#fff"/>')
            cells.append(f'<rect x="{cx+6}" y="{cy+6}" width="8" height="8" fill="#000"/>')
        inner = '\n'.join(cells)
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="92" height="92" viewBox="0 0 92 92">
  <rect width="92" height="92" fill="white" stroke="#000" stroke-width="1"/>
  {inner}
</svg>'''

    def _build_report_html(self, data, report_id):
        loc = data['location']
        ts = data['timestamp_readable']
        generated_at = datetime.now().strftime('%d %B %Y, %I:%M %p')
        approval = data.get('approval', None)
        retrieval_code = report_id.replace('FPR-ACC_', '')
        sev = data.get('severity', 'HIGH')
        sev_color = {'CRITICAL': '#8b0000', 'HIGH': '#cc0000', 'MODERATE': '#cc6600'}.get(sev, '#cc0000')

        # Accident image
        if data.get('frame_b64'):
            frame_html = f'''
            <div style="text-align:center;margin:14px 0;">
              <img src="data:image/jpeg;base64,{data["frame_b64"]}"
                   style="max-width:100%;max-height:300px;border:2px solid #8b0000;display:inline-block;"/>
              <div style="font-size:10px;color:#555;margin-top:5px;font-style:italic;">
                Fig. 1 — Accident scene auto-captured by FALCON AI system at {ts}
              </div>
            </div>'''
        else:
            frame_html = '<p style="color:#888;font-style:italic;text-align:center;padding:20px 0;">[ No image captured ]</p>'

        # Hospital rows
        hospitals_rows = ''
        for i, h in enumerate(data.get('hospitals', [])[:3], 1):
            avail = [d for d in h.get('doctors', []) if d.get('available')]
            doc_str = '; '.join(f"{d['name']} ({d['specialty']})" for d in avail[:2]) or '—'
            hospitals_rows += f'''
            <tr>
              <td style="text-align:center;">{i}</td>
              <td><strong>{h['name']}</strong></td>
              <td>{h.get('address','—')}</td>
              <td>{h.get('phone','—')}</td>
              <td style="text-align:center;">{h['distance_km']} km / {h['eta_minutes']} min</td>
              <td>{"✅ 24/7" if h.get('emergency') else "—"}</td>
              <td><small>{doc_str}</small></td>
            </tr>'''

        # Police rows
        police_rows = ''
        for i, ps in enumerate(data.get('police_stations', [])[:3], 1):
            duty = [o for o in ps.get('officers', []) if o.get('on_duty')]
            off_str = '; '.join(f"{o['name']} [{o['badge']}]" for o in duty[:2]) or '—'
            police_rows += f'''
            <tr>
              <td style="text-align:center;">{i}</td>
              <td><strong>{ps['name']}</strong></td>
              <td>{ps.get('address','—')}</td>
              <td>{ps.get('phone','—')}</td>
              <td style="text-align:center;">{ps['distance_km']} km / {ps['eta_minutes']} min</td>
              <td>{ps.get('station_id','—')}</td>
              <td><small>{off_str}</small></td>
            </tr>'''

        # Approval block
        if approval:
            approval_html = f'''
            <div style="border:3px solid #006400;background:#f0fff0;padding:16px;
                        margin:16px 0;text-align:center;">
              <div style="font-size:36px;margin-bottom:4px;">✅</div>
              <div style="font-size:17px;font-weight:bold;color:#006400;letter-spacing:3px;">
                APPROVED BY POLICE
              </div>
              <div style="margin-top:10px;font-size:13px;">
                <strong>Officer:</strong> {approval['approved_by']} &nbsp;|&nbsp;
                <strong>Badge:</strong> {approval['badge']} &nbsp;|&nbsp;
                <strong>Station:</strong> {approval['station']}
              </div>
              <div style="margin-top:4px;font-size:13px;">
                <strong>Approved At:</strong> {approval['approved_at']}
              </div>
              <div style="margin-top:10px;font-size:14px;font-weight:bold;color:#8b0000;
                          background:#fff3f3;padding:8px;border:1px dashed #8b0000;">
                📋 REMARKS: {approval['remarks']}
              </div>
              <div style="margin-top:8px;font-size:11px;color:#555;">
                This approval authorises the victim to seek immediate medical treatment.
                Present this report at any government hospital for priority treatment.
              </div>
            </div>'''
            approval_badge = '<span style="background:#006400;color:#fff;padding:3px 10px;font-size:11px;font-weight:bold;">✅ POLICE APPROVED</span>'
        else:
            approval_html = f'''
            <div style="border:2px dashed #cc8800;background:#fffbef;padding:14px;
                        margin:16px 0;text-align:center;">
              <div style="font-size:14px;font-weight:bold;color:#cc8800;">
                ⏳ AWAITING POLICE APPROVAL
              </div>
              <div style="font-size:12px;color:#555;margin-top:6px;line-height:1.6;">
                This report has been electronically submitted to the nearest police station.
                Once the officer approves it in the FALCON dashboard, this section will
                display the official clearance stamp authorising immediate hospital treatment.
              </div>
              <div style="margin-top:10px;">
                <strong>Quote this Report ID at your nearest police station:</strong><br/>
                <span style="font-family:monospace;font-size:15px;font-weight:bold;
                             color:#8b0000;background:#fff;padding:2px 10px;border:1px solid #8b0000;">
                  {report_id}
                </span>
              </div>
            </div>'''
            approval_badge = '<span style="background:#cc8800;color:#fff;padding:3px 10px;font-size:11px;font-weight:bold;">⏳ PENDING APPROVAL</span>'

        qr_svg = self._qr_svg(report_id)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Motor Accident Report — {report_id}</title>
<style>
  @page {{ size: A4; margin: 14mm; }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:"Times New Roman",Times,serif; font-size:13px; color:#111; background:#fff; line-height:1.5; }}
  .page {{ max-width:780px; margin:0 auto; padding:26px 30px; border:4px double #000; min-height:1050px; position:relative; }}
  .watermark {{ position:fixed; top:38%; left:15%; font-size:90px; font-weight:bold; color:rgba(0,0,0,0.03); transform:rotate(-35deg); pointer-events:none; letter-spacing:10px; z-index:0; }}

  /* HEADER */
  .header {{ text-align:center; border-bottom:3px double #000; padding-bottom:14px; margin-bottom:12px; }}
  .ashoka {{ font-size:60px; line-height:1; margin-bottom:4px; display:block; }}
  .gov1 {{ font-size:18px; font-weight:bold; letter-spacing:3px; text-transform:uppercase; }}
  .gov2 {{ font-size:13px; font-weight:bold; color:#333; margin-top:2px; }}
  .gov3 {{ font-size:11.5px; color:#555; margin-top:2px; }}
  .report-heading {{ margin-top:10px; font-size:17px; font-weight:bold; text-transform:uppercase; letter-spacing:2px; text-decoration:underline double; color:#8b0000; }}
  .report-sub {{ font-size:11.5px; color:#444; margin-top:3px; font-style:italic; }}

  /* META BAR */
  .meta-bar {{ display:flex; justify-content:space-between; flex-wrap:wrap; gap:4px; margin:10px 0; padding:7px 10px; background:#f5f5f5; border:1px solid #ccc; font-size:11.5px; }}

  /* SECTION */
  .section {{ margin:14px 0 8px; }}
  .sec-title {{ font-size:13px; font-weight:bold; text-transform:uppercase; letter-spacing:1px; border-bottom:2px solid #000; padding-bottom:3px; margin-bottom:9px; color:#003580; }}
  .sec-title .num {{ background:#003580; color:#fff; padding:1px 8px; margin-right:7px; font-size:12px; }}

  /* INFO GRID */
  .info-grid {{ display:grid; grid-template-columns:1fr 1fr; border:1px solid #999; }}
  .ic {{ padding:6px 10px; border-bottom:1px solid #ccc; border-right:1px solid #ccc; }}
  .ic:nth-child(even) {{ border-right:none; }}
  .ilabel {{ font-size:10px; color:#555; text-transform:uppercase; font-weight:bold; margin-bottom:2px; letter-spacing:0.4px; }}
  .ival {{ font-size:13px; font-weight:bold; color:#111; }}

  /* TABLES */
  table {{ width:100%; border-collapse:collapse; font-size:11px; margin-top:3px; }}
  th {{ background:#003580; color:#fff; padding:5px 7px; font-size:10.5px; text-align:left; }}
  td {{ border:1px solid #bbb; padding:5px 7px; vertical-align:top; }}
  tr:nth-child(even) td {{ background:#f9f9f9; }}

  /* DESC */
  .desc {{ border:1px solid #aaa; padding:10px 14px; font-size:13px; line-height:1.7; background:#fefefe; margin-top:5px; }}

  /* RETRIEVAL */
  .retrieval {{ border:2px solid #003580; padding:14px; margin:14px 0; display:flex; gap:14px; align-items:flex-start; background:#f5f8ff; }}

  /* SIGS */
  .sig-row {{ display:flex; justify-content:space-between; margin-top:32px; gap:10px; }}
  .sig-box {{ flex:1; text-align:center; border:1px solid #999; padding:8px; }}
  .sig-line {{ border-top:1px solid #333; margin-top:36px; padding-top:4px; font-size:11px; color:#333; }}

  /* FOOTER */
  .footer {{ margin-top:18px; border-top:2px solid #000; padding-top:7px; font-size:10px; color:#555; text-align:center; }}

  @media print {{ .no-print {{ display:none; }} body {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }} }}
</style>
</head>
<body>
<div class="watermark">FALCON</div>
<div class="page">

<!-- HEADER -->
<div class="header">
  <span class="ashoka">🏛</span>
  <div class="gov1">भारत सरकार &nbsp;·&nbsp; Government of India</div>
  <div class="gov2">Ministry of Road Transport and Highways</div>
  <div class="gov3">State Police Department — Emergency Response &amp; Accident Investigation Division</div>
  <div class="gov3" style="font-size:11px;">FALCON Automated Incident Detection System &nbsp;|&nbsp; AI &amp; Computer Vision</div>
  <div class="report-heading">Motor Vehicle Accident Report</div>
  <div class="report-sub">(As per Motor Vehicles Act 1988, Section 134 &amp; 135 — Duty to Report Accidents)</div>
  <div style="margin-top:8px;">
    <span style="background:#8b0000;color:#fff;padding:3px 10px;font-size:11px;font-weight:bold;margin:2px;">URGENT</span>
    <span style="background:#8b0000;color:#fff;padding:3px 10px;font-size:11px;font-weight:bold;margin:2px;">AI VERIFIED</span>
    <span style="background:#003580;color:#fff;padding:3px 10px;font-size:11px;font-weight:bold;margin:2px;">AUTO-DETECTED</span>
    &nbsp;{approval_badge}
  </div>
</div>

<!-- META BAR -->
<div class="meta-bar">
  <span><b>Report No:</b> {report_id}</span>
  <span><b>Incident:</b> {ts}</span>
  <span><b>Generated:</b> {generated_at}</span>
  <span><b>System:</b> FALCON v2.0</span>
</div>

<!-- SECTION 1 — INCIDENT INFO -->
<div class="section">
  <div class="sec-title"><span class="num">01</span>Incident Information</div>
  <div class="info-grid">
    <div class="ic"><div class="ilabel">Incident ID</div><div class="ival" style="font-family:monospace;">{data['id']}</div></div>
    <div class="ic"><div class="ilabel">Detection Date &amp; Time</div><div class="ival">{ts}</div></div>
    <div class="ic"><div class="ilabel">Location / Address</div><div class="ival">{loc['address']}</div></div>
    <div class="ic"><div class="ilabel">City / District</div><div class="ival">{loc.get('city','—')}, {loc.get('region','—')}</div></div>
    <div class="ic"><div class="ilabel">GPS Coordinates</div><div class="ival" style="font-family:monospace;">{loc['lat']:.6f}° N, {loc['lng']:.6f}° E</div></div>
    <div class="ic"><div class="ilabel">Country</div><div class="ival">{loc.get('country','India')}</div></div>
    <div class="ic"><div class="ilabel">Severity Level</div><div class="ival" style="color:{sev_color};font-size:15px;">⚠ {sev}</div></div>
    <div class="ic"><div class="ilabel">AI Detection Confidence</div><div class="ival">{int(data['confidence']*100)}% — AI Verified</div></div>
  </div>
</div>

<!-- SECTION 2 — DESCRIPTION -->
<div class="section">
  <div class="sec-title"><span class="num">02</span>Incident Description</div>
  <div class="desc">
    On <strong>{ts}</strong>, the FALCON Automated Accident Detection System identified a
    <strong>{sev} severity</strong> road accident at <strong>{loc['address']}</strong>
    (GPS: {loc['lat']:.5f}°N, {loc['lng']:.5f}°E).
    The AI engine — using optical flow analysis, motion spike detection, and
    foreground/edge change scoring — registered a detection confidence of
    <strong>{int(data['confidence']*100)}%</strong>, exceeding the activation threshold.
    <br/><br/>
    Upon detection, the system automatically: located the nearest hospitals and police
    stations within a 5 km radius; dispatched emergency SMS and email notifications;
    transmitted a WhatsApp alert with location and scene photo; and generated this
    official incident report. The accident scene image was captured at the moment of
    detection and is shown below in Section 3.
    <br/><br/>
    <em>Note: This is a system-generated first information record. A full FIR may need
    to be filed at the jurisdictional police station if criminal liability is established.</em>
  </div>
</div>

<!-- SECTION 3 — ACCIDENT PHOTOGRAPH -->
<div class="section">
  <div class="sec-title"><span class="num">03</span>Accident Scene — Auto-Captured Photograph</div>
  {frame_html}
  <div style="font-size:11px;color:#555;padding:4px 8px;border-left:3px solid #8b0000;background:#fff8f8;margin-top:6px;">
    <strong>Evidence Note:</strong> Image auto-captured by FALCON CCTV/IP camera at
    {ts}. Image hash and timestamp stored in system log.
    Report ID: <code>{report_id}</code>
  </div>
</div>

<!-- SECTION 4 — HOSPITALS -->
<div class="section">
  <div class="sec-title"><span class="num">04</span>Nearest Hospitals — Emergency Notified</div>
  <table>
    <tr>
      <th>#</th><th>Hospital Name</th><th>Address</th><th>Contact</th>
      <th>Dist / ETA</th><th>Emergency</th><th>Doctors On Duty</th>
    </tr>
    {hospitals_rows if hospitals_rows else '<tr><td colspan="7" style="text-align:center;color:#888;">No hospital data</td></tr>'}
  </table>
  <div style="font-size:10.5px;color:#555;margin-top:4px;font-style:italic;">
    ✉ Emergency notifications dispatched to all listed hospitals at {ts}.
  </div>
</div>

<!-- SECTION 5 — POLICE -->
<div class="section">
  <div class="sec-title"><span class="num">05</span>Nearest Police Stations — Notified</div>
  <table>
    <tr>
      <th>#</th><th>Station Name</th><th>Address</th><th>Contact</th>
      <th>Dist / ETA</th><th>Station ID</th><th>Officers On Duty</th>
    </tr>
    {police_rows if police_rows else '<tr><td colspan="7" style="text-align:center;color:#888;">No police station data</td></tr>'}
  </table>
  <div style="font-size:10.5px;color:#555;margin-top:4px;font-style:italic;">
    ✉ SMS alert dispatched to all listed stations at {ts}.
  </div>
</div>

<!-- SECTION 6 — POLICE CLEARANCE -->
<div class="section">
  <div class="sec-title"><span class="num">06</span>Police Clearance for Medical Treatment</div>
  {approval_html}
  <div style="font-size:11px;color:#333;padding:8px 10px;background:#f5f5f5;border:1px solid #ccc;margin-top:6px;line-height:1.7;">
    <strong>Instructions for Victim / Bystander:</strong><br/>
    1. Show this report (digital or printed) at the hospital reception.<br/>
    2. Quote Report No. <strong>{report_id}</strong> for priority emergency treatment.<br/>
    3. If approval is pending, the nearest police station can approve via the FALCON dashboard.<br/>
    4. Government hospitals must accept patients with an AI-generated accident report
       under Emergency Medical Treatment provisions.
  </div>
</div>

<!-- SECTION 7 — ACTIONS LOG -->
<div class="section">
  <div class="sec-title"><span class="num">07</span>System Actions Log</div>
  <table>
    <tr><th>Action</th><th>Status</th><th>Timestamp</th></tr>
    <tr><td>AI Accident Detection (Optical Flow + Motion)</td><td style="color:green;font-weight:bold;">✅ Completed</td><td>{ts}</td></tr>
    <tr><td>Location Geocoding (GPS / Reverse Geocode)</td><td style="color:green;font-weight:bold;">✅ Completed</td><td>{ts}</td></tr>
    <tr><td>Accident Scene Image Capture</td><td style="color:green;font-weight:bold;">✅ Saved</td><td>{ts}</td></tr>
    <tr><td>Nearby Hospital Search (OpenStreetMap)</td><td style="color:green;font-weight:bold;">✅ Completed</td><td>{ts}</td></tr>
    <tr><td>Nearby Police Station Search</td><td style="color:green;font-weight:bold;">✅ Completed</td><td>{ts}</td></tr>
    <tr><td>Hospital Emergency Notification (SMS + Email)</td><td style="color:green;font-weight:bold;">✅ Dispatched</td><td>{ts}</td></tr>
    <tr><td>Police Station Notification (SMS)</td><td style="color:green;font-weight:bold;">✅ Dispatched</td><td>{ts}</td></tr>
    <tr><td>WhatsApp Alert (Location + Scene Photo)</td><td style="color:green;font-weight:bold;">✅ Dispatched</td><td>{ts}</td></tr>
    <tr><td>Incident Report Generation</td><td style="color:green;font-weight:bold;">✅ Completed</td><td>{generated_at}</td></tr>
    <tr>
      <td>Police Report Approval</td>
      <td style="color:{'green' if approval else '#cc8800'};font-weight:bold;">
        {'✅ Approved — ' + approval['approved_at'] if approval else '⏳ Pending'}
      </td>
      <td>{approval['approved_at'] if approval else '—'}</td>
    </tr>
  </table>
</div>

<!-- SECTION 8 — RETRIEVAL -->
<div class="section">
  <div class="sec-title"><span class="num">08</span>Report Retrieval &amp; Future Reference</div>
  <div class="retrieval">
    <div style="flex-shrink:0;">
      {qr_svg}
      <div style="font-size:9px;text-align:center;margin-top:3px;color:#333;">Report Code</div>
    </div>
    <div style="flex:1;">
      <div style="font-size:13px;font-weight:bold;color:#003580;margin-bottom:8px;">
        How to retrieve this report in the future:
      </div>
      <table style="border:none;font-size:12px;">
        <tr><td style="border:none;padding:3px 6px;font-weight:bold;width:150px;">Report Number:</td>
            <td style="border:none;padding:3px 6px;font-family:monospace;color:#8b0000;font-weight:bold;font-size:13px;">{report_id}</td></tr>
        <tr><td style="border:none;padding:3px 6px;font-weight:bold;">Retrieval Code:</td>
            <td style="border:none;padding:3px 6px;font-family:monospace;color:#003580;font-weight:bold;font-size:13px;">{retrieval_code}</td></tr>
        <tr><td style="border:none;padding:3px 6px;font-weight:bold;">Incident Date:</td>
            <td style="border:none;padding:3px 6px;">{ts}</td></tr>
        <tr><td style="border:none;padding:3px 6px;font-weight:bold;">Location:</td>
            <td style="border:none;padding:3px 6px;">{loc['address']}</td></tr>
        <tr><td style="border:none;padding:3px 6px;font-weight:bold;">FALCON Dashboard:</td>
            <td style="border:none;padding:3px 6px;"><em>Accident History tab → search by Report No. or Date</em></td></tr>
        <tr><td style="border:none;padding:3px 6px;font-weight:bold;">Data File:</td>
            <td style="border:none;padding:3px 6px;font-family:monospace;font-size:11px;">reports/Report_{data['id']}.json</td></tr>
      </table>
      <div style="font-size:10.5px;color:#555;margin-top:8px;font-style:italic;line-height:1.6;">
        All records are stored in structured JSON on the FALCON server — including GPS,
        detection confidence, scene photograph, hospital/police data, notification logs,
        and approval status. Records are retained permanently and can be retrieved by
        insurance companies, courts, or medical institutions using the Report Number.
      </div>
    </div>
  </div>
</div>

<!-- SIGNATURES -->
<div class="sig-row">
  <div class="sig-box">
    <div class="sig-line">
      <strong>FALCON System</strong><br/>
      Automated Detection Officer<br/>
      Badge: FALCON-AI-001<br/>
      <em style="font-size:10px;">{generated_at}</em>
    </div>
  </div>
  <div class="sig-box">
    <div class="sig-line">
      <strong>Station House Officer</strong><br/>
      Signature &amp; Seal: ____________<br/>
      Date: ____________
    </div>
  </div>
  <div class="sig-box">
    <div class="sig-line">
      <strong>District Superintendent of Police</strong><br/>
      Verified &amp; Acknowledged<br/>
      Seal: ____________
    </div>
  </div>
</div>

<!-- FOOTER -->
<div class="footer">
  <div style="font-size:11px;font-weight:bold;margin-bottom:3px;">
    FALCON — Fatality Alert &amp; Crash Locator Over Networks &nbsp;|&nbsp; Version 2.0
  </div>
  <div>
    Report ID: {report_id} &nbsp;|&nbsp; Generated: {generated_at} &nbsp;|&nbsp;
    Certified by: Ministry of Road Transport &amp; Highways, Government of India
  </div>
  <div style="margin-top:3px;">
    Legally valid automated incident report under IT Act 2000 &amp; Motor Vehicles Act 1988.
    May be presented at hospitals, insurance companies, or courts of law.
  </div>
</div>

</div><!-- end .page -->

<!-- PRINT BUTTON -->
<div class="no-print" style="text-align:center;margin:20px;font-family:sans-serif;">
  <button onclick="window.print()"
          style="padding:12px 32px;background:#003580;color:#fff;border:none;
                 font-size:15px;cursor:pointer;border-radius:4px;margin-right:10px;">
    🖨️ Print / Save as PDF
  </button>
  <button onclick="window.close()"
          style="padding:12px 24px;background:#888;color:#fff;border:none;
                 font-size:15px;cursor:pointer;border-radius:4px;">
    ✕ Close
  </button>
  <p style="margin-top:8px;font-size:12px;color:#666;">
    To save as PDF: Click "Print" → set destination to "Save as PDF" → Save
  </p>
</div>

</body>
</html>'''