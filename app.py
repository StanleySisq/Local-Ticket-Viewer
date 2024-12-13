from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
import db_functions  
import threading
import time

app = Flask(__name__)

db_functions.create_base()
db_functions.start_log()

@app.route('/')
def index():
    tickets = db_functions.get_all_tickets()
    return render_template('index.html', tickets=tickets)

@app.route('/tickets_json')
def tickets_json():
    tickets = db_functions.get_all_tickets()
    tickets_list = [{'id': ticket['id'], 'title': ticket['title'], 'contact': ticket['contact'], 
                     'client': ticket['client'], 'gid': ticket['gid'], 'visible': ticket['visible'], 
                     'mrygacz': ticket['mrygacz'], 'uploaded': ticket['uploaded'], 'link': ticket['link']} for ticket in tickets]
    return jsonify(tickets_list)

def update_mrygacz(ticket_id):
    time.sleep(120)  # How long new ticket blink
    db_functions.update_ticket_mrygacz(ticket_id, "False")  
    db_functions.write_log(f"Ticket {ticket_id} migacz OFF")

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        contact = request.form['contact']
        client = request.form['client']
        gid = request.form['gid']
        link = request.form['link']
        ticket_id = db_functions.add_ticket(title, contact, client, gid, link)

        threading.Thread(target=update_mrygacz, args=(ticket_id,)).start()
        db_functions.write_log(f"Ticket {ticket_id} MANUAL ADD")
        
        return redirect(url_for('index'))
    return render_template('add_ticket.html')

@app.route('/delete/<int:ticket_id>', methods=['POST'])
def delete(ticket_id):
    existing_ticket = db_functions.get_ticket_by_id(ticket_id)
    if not existing_ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    db_functions.delete_ticket(ticket_id)
    db_functions.write_log(f"Ticket {ticket_id} MANUAL DELETE")

    return redirect(url_for('index'))

@app.route('/select_ticket')
def select_ticket():
    tickets = db_functions.get_all_tickets() 
    return render_template('select_ticket.html', tickets=tickets)

@app.route('/update/<int:ticket_id>', methods=['GET', 'POST'])
def update(ticket_id):
    ticket = db_functions.get_ticket_by_id(ticket_id)
    
    if not ticket:
        return f"Ticket o ID {ticket_id} nie istnieje.", 404

    if request.method == 'POST':
        title = request.form.get('title')
        contact = request.form.get('contact')
        client = request.form.get('client')
        gid = request.form.get('gid')
        visible = request.form.get('visible')
        mrygacz = request.form.get('mrygacz')

        db_functions.update_ticket(ticket_id, title, contact, client, gid, visible)
        db_functions.update_ticket_mrygacz(ticket_id, mrygacz)
        db_functions.write_log(f"Ticket {ticket_id} MANUAL UPDATE")

        return redirect(url_for('select_ticket'))

    return render_template('update_ticket.html', ticket=ticket)

@app.route('/api/tickets', methods=['POST'])
def add_ticket():
    if request.is_json:
        data = request.get_json() 
    else:
        data = {
            'title': request.form.get('title'),
            'contact': request.form.get('contact'),
            'client': request.form.get('client'),
            'gid': request.form.get('gid'),
            'link': request.form.get('link')
        }

    title = data.get('title')
    contact = data.get('contact')
    client = data.get('client')
    gid = data.get('gid')
    link = data.get('link')

    if not all([title, contact, client, gid]):
        db_functions.write_log(f"Ticket API ADD missing DATA 400 {data}")
        return jsonify({'error': 'Missing data fields'}), 400

    ticket_id = db_functions.add_ticket(title, contact, client, gid, link)

    threading.Thread(target=update_mrygacz, args=(ticket_id,)).start()
    db_functions.write_log(f"Ticket {ticket_id} API ADD migacz ON 201")

    return jsonify({'message': 'Ticket added successfully', 'ticket_id': ticket_id}), 201

@app.route('/api/tickets/<int:ticket_id>', methods=['PUT', 'PATCH'])
def update_ticket(ticket_id):
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    existing_ticket = db_functions.get_ticket_by_id(ticket_id)

    if not existing_ticket:
        db_functions.write_log(f"Ticket {ticket_id} API UPDATE - DOES NOT EXIST 404")
        return jsonify({'error': 'Ticket not found'}), 404
    
    title = data.get('title') if data.get('title') else existing_ticket[1]
    contact = data.get('contact') if data.get('contact') else existing_ticket[2]
    client = data.get('client') if data.get('client') else existing_ticket[3]
    gid = data.get('gid') if data.get('gid') else existing_ticket[4]
    visible = data.get('visible') if data.get('visible') else existing_ticket[5]
    mrygacz = data.get('mrygacz') if data.get('mrygacz') else existing_ticket[6]

    db_functions.update_ticket(ticket_id, title, contact, client, gid, visible)
    db_functions.write_log(f"Ticket {ticket_id} API UPDATE 200")

    return jsonify({'message': 'Ticket updated successfully'}), 200

@app.route('/api/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    existing_ticket = db_functions.get_ticket_by_id(ticket_id)
    if not existing_ticket:
        return jsonify({'error': 'Ticket not found'}), 404

    db_functions.delete_ticket(ticket_id)
    db_functions.write_log(f"Ticket {ticket_id} API DELETE 200")

    return jsonify({'message': 'Ticket deleted successfully'}), 200

@app.route('/api/vacation', methods=['POST'])
def save_vacation():
    data = request.get_json() 
    name = data.get('name')
    vacation_type = data.get('type')

    if not name or vacation_type not in ['vacation', 'remote']:
        return jsonify({'error': 'Invalid request'}), 400

    if vacation_type == "vacation":
        with open("absence.txt", "a", encoding='utf-8') as file:
            file.write(name + '\n')
    elif vacation_type == "remote":
        with open("remote.txt", "a", encoding='utf-8') as file:
            file.write(name + '\n')

    db_functions.write_log(f"{type} updated successfully, {name}")

    return jsonify({'message': 'Vacation updated successfully'}), 200

@app.route('/api/vacation_clear', methods=['DELETE'])
def clear_vacation():
    with open("absence.txt", 'w', encoding='utf-8') as file:
        pass
    with open("remote.txt", 'w', encoding='utf-8') as file:
        pass

    db_functions.write_log(f"Vacation cleared successfully")

    return jsonify({'message': 'Cleared successfully'}), 200

@app.route('/remote_people')
def get_remote_people():
    try:
        with open('remote.txt', 'r', encoding='utf-8') as file: 
            people = [line.strip() for line in file if line.strip()]
        return jsonify({'people': people})
    except FileNotFoundError:
        return jsonify({'people': []})

@app.route('/absent_people')
def get_absent_people():
    try:
        with open('absence.txt', 'r', encoding='utf-8') as file:
            absent_people = [line.strip() for line in file if line.strip()]
        return jsonify({'people': absent_people})
    except FileNotFoundError:
        return jsonify({'people': []})

ip_ban_list = ['10.70.66.17']

#@app.before_request
def block_method():
    ip = request.environ.get('REMOTE_ADDR')
    if ip in ip_ban_list:
        abort(403)

if __name__ == '__main__':
    app.run(debug=False, host='172.17.17.70', port=5000)