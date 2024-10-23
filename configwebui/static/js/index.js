var editor;
var myschema;
const pathName = window.location.pathname;
const configRoot = pathName.split('/').pop();
const statusBarElement = document.querySelector('#status-bar');
const statusIconElement = document.querySelector('#status-icon');

function flashMessage(message, category) {
    const flashMessageElement = document.querySelector('#flash-messages');
    const messageHTML = `<div class="alert alert-${category}"><button type="button" class="close" data-dismiss="alert">&times;</button><span>${message}</span></div>`;
    flashMessageElement.insertAdjacentHTML('beforeend', messageHTML);
    window.scroll({
        top: 0,
        behavior: 'smooth' // 平滑滚动
    });
    return messageHTML;
}

function clearFlashMessage() {
    const flashMessageElement = document.querySelector('#flash-messages');
    flashMessageElement.innerHTML = '';
}

function changeCheckboxStyleBootstrap4() {
    const container = document.querySelector("#editor-container");
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(input => {
        const parent = input.parentElement;
        const newLabel = document.createElement("label");
        newLabel.setAttribute("for", input.id);
        input.className += " custom-control-input";

        if (parent.classList.contains('custom-control') && parent.classList.contains('custom-checkbox')) {
            return;
        }
        if (parent.tagName.toLowerCase() === 'label') {
            parent.removeAttribute('for');
            parent.className = "custom-control custom-checkbox";
            newLabel.className = "custom-control-label checkbox-plain";
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'span') {
            parent.className = "custom-control custom-checkbox d-inline-flex";
            newLabel.className = "custom-control-label checkbox-heading";

            parent.childNodes.forEach(child => {
                if (child.nodeType === Node.TEXT_NODE && child.textContent.trim() !== "") {
                    newLabel.appendChild(child);
                }
            });
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'b') {
            parent.className = "custom-control custom-checkbox user-add";
            newLabel.className = "custom-control-label checkbox-plain";

            parent.insertBefore(newLabel, input.nextSibling);

            const newParent = document.createElement('label');
            while (parent.firstChild) {
                newParent.appendChild(parent.firstChild);
            }
            Array.from(parent.attributes).forEach(attr => {
                newParent.setAttribute(attr.name, attr.value);
            });
            parent.replaceWith(newParent);
        }
    });
}

function changeCheckboxStyle() {
    changeCheckboxStyleBootstrap4();
    const container = document.querySelector("#editor-container");
    const saveButtons = container.querySelectorAll('.json-editor-btntype-save');
    saveButtons.forEach(button => {
        button.addEventListener('click', changeCheckboxStyleBootstrap4);
    });
    const addButtons = container.querySelectorAll('.json-editor-btntype-add');
    addButtons.forEach(button => {
        button.addEventListener('click', changeCheckboxStyleBootstrap4);
    });
}

function navigateToConfig() {
    const selectElement = document.getElementById("configSelect");
    const selectedValue = selectElement.value;
    if (selectedValue) {
        window.location.href = selectedValue;
    } else {
        window.location.href = "/";
    }
}



async function getConfigAndSchema() {
    var res = {};
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
    // Validate the editor's current value against the schema
    const errors = editor.validate();

    if (errors.length) {
        errors.forEach(error => {
            const parts = error.path.split('.');
            const result = parts.map((part, index) => {
                return index >= 1 ? `[${part}]` : part;
            });

            const href = result.join('');
            flashMessage(`Property "<b>${error.property}</b>" unsatisfied at {<a href="#${href}" class="alert-link">${error.path}</a>}: ${error.message}`, 'danger');
        });
        return;
    }
    const configValue = JSON.stringify(editor.getValue());
    try {
        const response = await fetch(`/api${pathName}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: configValue
        });
        const data = await response.json();
        var messageCategory;
        if (data.success) {
            messageCategory = 'success';
        } else {
            messageCategory = 'danger';
        }
        for (const message of data.messages) {
            flashMessage(message, messageCategory);
        }

    } catch (error) {
        flashMessage('Failed to save config. Checkout your python backend.', 'danger');
    }
}


async function reload() {
    clearFlashMessage();
    const configAndSchema = await getConfigAndSchema();
    editor.setValue(configAndSchema.config);
}

async function launch() {
    clearFlashMessage();
    try {
        flashMessage("Trying to launch the main program. Go back and check out your terminal.", "info");
        await fetch(`/api/launch`, {
            method: 'GET',
        });
    } catch (error) {
        flashMessage('Failed to launch the main program. Check your python backend.', 'danger');
    }
}

async function terminate() {
    clearFlashMessage();
    try {
        flashMessage("Trying to terminate the editor backend. Subsequent changes will not be saved.", "warning");
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
        theme: 'bootstrap4',
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
        document.querySelector('#json-preview').textContent = JSON.stringify(editor.getValue(), null, 2);
    });
    editor.on('ready', function () {
        changeCheckboxStyle();
        statusBarElement.style.display = 'none';
    });
}

initialize_editor();

const saveActionButtons = document.querySelectorAll('.save-action');
saveActionButtons.forEach(button => {
    button.addEventListener('click', saveConfig);
});

const resetActionButtons = document.querySelectorAll('.reset-action');
resetActionButtons.forEach(button => {
    button.addEventListener('click', reload);
});

const launchActionButtons = document.querySelectorAll('.launch-action');
launchActionButtons.forEach(button => {
    button.addEventListener('click', launch);
});

const terminateActionButtons = document.querySelectorAll('.terminate-action');
terminateActionButtons.forEach(button => {
    button.addEventListener('click', terminate);
});
