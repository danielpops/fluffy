from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request

from fluffy import app
from fluffy.backends import get_backend
from fluffy.highlighting import UI_LANGUAGES_MAP
from fluffy.models import FileTooLargeError
from fluffy.models import HtmlToStore
from fluffy.models import UploadedFile
from fluffy.utils import human_size
from fluffy.utils import ONE_MB


@app.route('/')
def home():
    return render_template(
        'home.html',
        languages=sorted(
            UI_LANGUAGES_MAP.items(),
            key=lambda key_val: key_val[1],
        ),
    )


@app.route('/upload', methods={'POST'})
def upload():
    """Process an upload and return JSON status."""
    uploaded_files = []
    for f in request.files.getlist('file'):
        try:
            with UploadedFile.from_http_file(f) as uf:
                get_backend().store_object(uf)
            uploaded_files.append(uf)
        except FileTooLargeError:
            return jsonify({
                'success': False,
                'error': '{} exceeded the maximum file size limit of {}'.format(
                    f.filename,
                    human_size(app.config['MAX_UPLOAD_SIZE']),
                ),
            })

    with HtmlToStore.from_html(render_template(
        'details.html',
        uploads=uploaded_files,
    )) as details_obj:
        get_backend().store_html(details_obj)

    url = app.config['HTML_URL'].format(name=details_obj.name)

    if 'json' in request.args:
        return jsonify({
            'success': True,
            'redirect': url,
        })
    else:
        return redirect(url)


@app.route('/paste', methods={'POST'})
def paste():
    """Paste and redirect."""
    text = request.form['text']

    # TODO: make this better
    assert 1 <= len(text) <= ONE_MB, len(text)

    with HtmlToStore.from_html(render_template(
        'paste.html',
        text=text,
        language=request.form['language'],
    )) as paste_obj:
        get_backend().store_html(paste_obj)

    url = app.config['HTML_URL'].format(name=paste_obj.name)
    return redirect(url)