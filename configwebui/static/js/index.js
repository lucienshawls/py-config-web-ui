'use strict';
let editor;
let editor_is_ready = false;
const pathName = window.location.pathname;
const configRoot = pathName.split('/').pop();
const statusBarElement = document.querySelector('#status-bar');
const statusIconElement = document.querySelector('#status-icon');
const jsonPreviewTextElement = document.querySelector('#json-preview-text');
const mainOutputTextElement = document.querySelector('#main-output-text');
const saveOutputTextElement = document.querySelector('#save-output-text');

function flashMessage(message, category) {
    const flashMessageElement = document.querySelector('#flash-messages');
    const messageHTML = `<div class="alert alert-${category} alert-dismissible fade show" role="alert"><div>${message}</div><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
    flashMessageElement.insertAdjacentHTML('beforeend', messageHTML);
    window.scroll({
        top: 0,
        behavior: 'smooth'
    });
    return messageHTML;
}

function clearFlashMessage() {
    const flashMessageElement = document.querySelector('#flash-messages');
    flashMessageElement.innerHTML = '';
}

function changeCheckboxStyle() {
    const container = document.querySelector('#editor-container');
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(input => {
        if (input.parentElement.tagName.toLowerCase() === 'span' && input.parentElement.attributes.length === 0) {
            // Get it out of span
            const parentSpan = input.parentElement;
            const parentOfParent = parentSpan.parentElement;
            while (parentSpan.firstChild) {
                parentOfParent.insertBefore(parentSpan.firstChild, parentSpan);
            }
            parentSpan.remove();
        }

        const parent = input.parentElement;
        const newLabel = document.createElement('label');
        newLabel.setAttribute('for', input.id);

        parent.removeAttribute('for');
        if (parent.classList.contains('form-check')) {
            return;
        }

        input.className += ' form-check-input editor-check-input';
        if (parent.tagName.toLowerCase() === 'label') {
            input.className += ' check-input-plain';
            parent.className = 'form-check editor-check';
            newLabel.className = 'form-check-label check-label-plain';
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'span') {
            input.className += ' check-input-heading';
            parent.className = 'form-check editor-check d-inline-flex';
            newLabel.className = 'form-check-label check-label-heading';

            parent.childNodes.forEach(child => {
                if (child.nodeType === Node.TEXT_NODE && child.textContent.trim() !== '') {
                    newLabel.appendChild(child);
                }
            });
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'b') {
            input.className += ' check-input-plain';
            parent.className = 'form-check editor-check user-add-item';
            newLabel.className = 'form-check-label check-label-plain';

            parent.insertBefore(newLabel, input.nextSibling);

            const newParent = document.createElement('label');
            while (parent.firstChild) {
                newParent.appendChild(parent.firstChild);
            }
            parent.attributes.forEach(attr => {
                newParent.setAttribute(attr.name, attr.value);
            });
            parent.replaceWith(newParent);
        }
    });
}
function changeButtonGroupStyle() {
    const buttonGroups = document.querySelectorAll('span.btn-group');
    buttonGroups.forEach(buttonGroup => {
        if (buttonGroup.style.display === 'inline-block') {
            buttonGroup.removeAttribute('style');
        }
        if (buttonGroup.querySelector('button.json-editor-btntype-delete') !== null) {
            buttonGroup.classList.add('mb-1');
        }
    });
}

function setAnchor() {
    document.querySelectorAll('[data-schemapath]').forEach(element => {
        if (!element.id) {
            const dataSchemaPath = element.getAttribute('data-schemapath')
            // root.a.b.c => root[a][b][c]
            const parts = dataSchemaPath.split('.');
            const anchor = parts.map((part, index) => {
                return index >= 1 ? `[${part}]` : part;
            }).join('');

            element.id = anchor;
        }
    });
}

function changeStyle() {
    changeCheckboxStyle();
    changeButtonGroupStyle();
    setAnchor();
}

function navigateToConfig() {
    const selectElement = document.getElementById('configSelect');
    const selectedValue = selectElement.value;
    if (selectedValue) {
        window.location.href = selectedValue;
    } else {
        window.location.href = '/';
    }
}

async function getConfigAndSchema() {
    let res = {};
    const pathName = window.location.pathname;
    try {
        const response = await fetch('/api' + pathName, { method: 'GET' });
        const data = await response.json();
        res.config = data.config;
        res.schema = data.schema;
        if (data.success) {
            statusIconElement.className = 'spinner-border text-success';
        }
        else {
            statusIconElement.className = 'spinner-border text-danger';
            flashMessage('Failed to get config from server', 'danger');
        }
    }
    catch (error) {
        flashMessage('Failed to get config from server', 'danger');
        statusIconElement.className = 'spinner-border text-danger';
    }
    return res;
}

async function saveConfig() {
    clearFlashMessage();
    const errors = editor.validate();

    if (errors.length) {
        errors.forEach(error => {
            // root.a.b.c => root[a][b][c]
            const parts = error.path.split('.');
            const href = parts.map((part, index) => {
                return index >= 1 ? `[${part}]` : part;
            }).join('');

            flashMessage(`Property "<b>${error.property}</b>" unsatisfied at {<a href="#${href}" class="alert-link">${error.path}</a>}: ${error.message}`, 'danger');
        });
        return;
    }
    const configValue = JSON.stringify(editor.getValue());
    try {
        const response = await fetch(`/api${pathName}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: configValue
        });
        const data = await response.json();
        let messageCategory;
        if (data.success) {
            messageCategory = 'success';
        } else {
            messageCategory = 'danger';
        }
        for (const message of data.messages) {
            flashMessage(message, messageCategory);
        }
        return data.success;
    } catch (error) {
        flashMessage('Failed to save config. Checkout your python backend.', 'danger');
        return false;
    }
}


async function reload() {
    clearFlashMessage();
    const configAndSchema = await getConfigAndSchema();
    editor.setValue(configAndSchema.config);
    setTimeout(() => changeStyle(), 0);
}

async function launch() {
    clearFlashMessage();
    try {
        const response = await fetch(`/api/launch`, {
            method: 'GET',
        });
        const data = await response.json();
        let messageCategory;
        if (data.success) {
            messageCategory = 'success';
        } else {
            messageCategory = 'danger';
        }
        for (const message of data.messages) {
            flashMessage(message, messageCategory);
        }
        return data.success;
    } catch (error) {
        flashMessage('Failed to launch main program. Check your python backend.', 'danger');
        return false;
    }
}

async function terminate() {
    clearFlashMessage();
    try {
        flashMessage('Trying to terminate the editor backend. Subsequent changes will not be saved.', 'warning');
        await fetch(`/api/shutdown`, {
            method: 'GET',
        });
    } catch (error) {
        flashMessage('Failed to terminate the editor backend. Maybe it is already terminated.', 'danger');
    }
}

async function initialize_editor() {
    statusIconElement.className = 'spinner-border text-primary';
    statusBarElement.style.display = 'block';
    const configAndSchema = await getConfigAndSchema();
    const myschema = configAndSchema.schema;
    const myconfig = configAndSchema.config;
    const jsonEditorConfig = {
        form_name_root: configRoot,
        iconlib: 'fontawesome5',
        theme: 'bootstrap5',
        show_opt_in: true,
        disable_edit_json: true,
        disable_properties: true,
        disable_collapse: false,
        enable_array_copy: true,
        no_additional_properties: true,
        enforce_const: true,
        startval: myconfig,
        schema: myschema
    };
    editor = new JSONEditor(document.querySelector('#editor-container'), jsonEditorConfig);
    editor.on('change', function () {
        if (editor_is_ready) {
            setTimeout(() => changeStyle(), 0);
            jsonPreviewTextElement.textContent = JSON.stringify(editor.getValue(), null, 2);
        }
    });
    editor.on('ready', function () {
        editor_is_ready = true;
        setTimeout(() => changeStyle(), 0);
        statusBarElement.style.display = 'none';
        jsonPreviewTextElement.wrap = "off";
    });
}

initialize_editor();

function get_output(func_type) {
    let complete = true;
    const intervalId = setInterval(async () => {
        if (!complete) {
            return;
        }
        let outputElement;
        let url;
        let err_message;
        if (func_type === 'main') {
            outputElement = mainOutputTextElement;
            url = `/api/get_main_output`;
            err_message = 'Failed to get output from the main program.';
        } else if (func_type === 'save') {
            outputElement = saveOutputTextElement;
            url = `/api${pathName}/get_save_output`;
            err_message = 'Failed to get output from the data-saving script.';
        } else {
            clearInterval(intervalId);
            return;
        }
        try {
            complete = false;
            const response = await fetch(url, {
                method: 'GET',
            });
            const data = await response.json();

            let scroll = false;
            if (outputElement.scrollTop + outputElement.clientHeight >= outputElement.scrollHeight) {
                scroll = true;
            }
            outputElement.wrap = "off";
            outputElement.value = data.output + data.error;
            if (scroll) {
                outputElement.scrollTop = outputElement.scrollHeight;
            }
            if (!data.running) {
                clearInterval(intervalId);
            }
        } catch (error) {
            flashMessage(err_message, 'danger');
            clearInterval(intervalId);
        }
        complete = true;
    }, 200);
}

const saveActionButtons = document.querySelectorAll('.save-action');
saveActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        if (await saveConfig()) {
            get_output('save');
        }
    });
});

const resetActionButtons = document.querySelectorAll('.reset-action');
resetActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        await reload();
    });
});

const launchActionButtons = document.querySelectorAll('.launch-action');
launchActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        if (await launch()) {
            get_output('main');
        }
    });
});

const terminateActionButtons = document.querySelectorAll('.terminate-action');
terminateActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        await terminate();
    });
});
