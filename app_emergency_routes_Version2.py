from flask import Blueprint, render_template, request, redirect, url_for, current_app, send_file
from flask_login import login_required, current_user
import io, json, qrcode
from yourapp import db
from .models_emergency import EmergencyCard, EmergencyContact
import pathlib

bp = Blueprint('emergency', __name__, url_prefix='/emergency')

@bp.route('/generate', methods=['GET','POST'])
@login_required
def generate_card():
    lang = request.args.get('lang', 'en')
    # gather user's allergies/meds from models or placeholders:
    allergies = [a.name for a in getattr(current_user, 'allergens', [])]
    meds = getattr(current_user, 'medications', [])
    qr_payload = {"name": current_user.username, "user_id": current_user.id, "allergies": allergies, "meds": meds}
    qr_img = qrcode.make(json.dumps(qr_payload))
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    buf.seek(0)

    # save file
    upload_folder = pathlib.Path(current_app.config.get('UPLOAD_FOLDER', 'instance/uploads'))
    upload_folder.mkdir(parents=True, exist_ok=True)
    card = EmergencyCard(user_id=current_user.id, lang=lang, qr_data=json.dumps(qr_payload))
    db.session.add(card)
    db.session.commit()
    filepath = upload_folder / f'card_{card.id}.png'
    with open(filepath, 'wb') as f:
        f.write(buf.getvalue())
    card.filename = str(filepath)
    db.session.commit()
    return redirect(url_for('emergency.view_card', card_id=card.id))

@bp.route('/view/<int:card_id>')
@login_required
def view_card(card_id):
    card = EmergencyCard.query.get_or_404(card_id)
    return send_file(card.filename, mimetype='image/png')