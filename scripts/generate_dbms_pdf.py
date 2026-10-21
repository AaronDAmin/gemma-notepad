"""Generate exact pixel-faithful DBMS_Chapter1.pdf matching reference image."""
import fitz

page_w, page_h = 760, 840
doc = fitz.open()

bg_col = (0.988, 0.965, 0.925) # #FCF6EC

for i in range(20):
    page = doc.new_page(width=page_w, height=page_h)
    page.draw_rect(page.rect, color=bg_col, fill=bg_col)
    
    if i == 0:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        body {
            font-family: 'Segoe UI', -apple-system, sans-serif;
            color: #282B28;
            margin: 0;
            padding: 0;
        }
        .ch-num {
            font-family: 'Segoe UI', sans-serif;
            color: #C28828;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 12px;
            letter-spacing: 0.2px;
        }
        .ch-title {
            font-family: 'Georgia', serif;
            color: #1A1C1A;
            font-size: 36px;
            font-weight: bold;
            line-height: 1.15;
            margin-top: 0px;
            margin-bottom: 30px;
            letter-spacing: -0.4px;
        }
        .sec-num {
            color: #C28828;
            font-size: 16px;
            font-weight: 700;
            margin-top: 24px;
            margin-bottom: 12px;
        }
        .body-p {
            font-size: 14.5px;
            line-height: 1.62;
            color: #282B28;
            margin-bottom: 16px;
            text-align: justify;
        }
        ul {
            margin-top: 8px;
            margin-bottom: 14px;
            padding-left: 24px;
        }
        li {
            font-size: 14.5px;
            line-height: 1.62;
            color: #282B28;
            margin-bottom: 5px;
        }
        li::marker {
            color: #C28828;
        }
        </style>
        </head>
        <body>
        <div class='ch-num'>Chapter 1</div>
        <div class='ch-title'>Database Management<br>Systems</div>
        <div class='sec-num'>1.1 &nbsp; Introduction</div>
        <div class='body-p'>
        A database management system (DBMS) is a software system that allows users to define, create, maintain, and control access to a database. It provides an organized way to store, retrieve, and manage data efficiently.
        </div>
        <div class='body-p'>
        A DBMS acts as an interface between users and the data stored in the database. It ensures data consistency, security, and concurrency control while providing tools for data manipulation and querying.
        </div>
        <div class='sec-num'>1.2 &nbsp; Objectives of a DBMS</div>
        <div class='body-p'>The main objectives of a DBMS include:</div>
        <ul>
            <li>Efficient storage and retrieval of data.</li>
            <li>Minimization of data redundancy.</li>
            <li>Data integrity and consistency.</li>
        </ul>
        </body>
        </html>
        """
        # Rect indented with 72px left margin, 65px top margin
        rect = fitz.Rect(72, 65, page_w - 72, page_h - 60)
        page.insert_htmlbox(rect, html)
        
        # Bottom-right pill 1 / 20
        pill_rect = fitz.Rect(page_w - 145, page_h - 75, page_w - 85, page_h - 45)
        page.draw_rect(pill_rect, color=(0.94, 0.88, 0.77), fill=(0.94, 0.88, 0.77), radius=0.45)
        page.insert_text((page_w - 130, page_h - 55), '1 / 20', fontsize=12, color=(0.16, 0.17, 0.16), fontname='helv')
    else:
        page.insert_text((72, 70), f'Chapter 1: Database Management Systems - Page {i+1}', fontsize=12, color=(0.5, 0.5, 0.5), fontname='helv')
        pill_rect = fitz.Rect(page_w - 145, page_h - 75, page_w - 85, page_h - 45)
        page.draw_rect(pill_rect, color=(0.94, 0.88, 0.77), fill=(0.94, 0.88, 0.77), radius=0.45)
        page.insert_text((page_w - 130, page_h - 55), f'{i+1} / 20', fontsize=12, color=(0.16, 0.17, 0.16), fontname='helv')

doc.save('assets/DBMS_Chapter1.pdf')
print('assets/DBMS_Chapter1.pdf generated successfully!')
page0 = doc[0]
rects = page0.search_for('database management system (DBMS)')
print('Search rects for highlighted text:', rects)
