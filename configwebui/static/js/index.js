function flashMessage(message, category) {
    const flashMessageElement = document.querySelector('#flash-messages');
    const messageHTML = `<div class="alert alert-${category}"><button type="button" class="close" data-dismiss="alert">&times;</button>${message}</div>`;
    flashMessageElement.insertAdjacentHTML('beforeend', messageHTML);
}

function clearFlashMessage() {
    const flashMessageElement = document.querySelector('#flash-messages');
    flashMessageElement.innerHTML = '';
}

function changeCheckboxStyle() {
    const container = document.querySelector("#editor-container");
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(input => {
        const parent = input.parentElement;
        if (parent.tagName.toLowerCase() === 'label') {
            parent.removeAttribute('for');
            parent.className = "custom-control custom-checkbox";
            input.className += " custom-control-input";

            const newLabel = document.createElement("label");
            newLabel.className = "custom-control-label";
            newLabel.setAttribute("for", input.id);
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'span') {
            // parent.className = "custom-control custom-checkbox";
            // input.className += " custom-control-input";

            // const newLabel = document.createElement("label");
            // newLabel.className = "custom-control-label";
            // newLabel.setAttribute("for", input.id);
            // parent.insertBefore(newLabel, input.nextSibling);
        }
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
        console.log('Success:', data);
        res.config = data.config;
        res.schema = data.schema;
    }
    catch (error) {
        console.error('Error:', error);
    }
    return res;
}

async function saveConfig() {
    clearFlashMessage();
    const pathName = window.location.pathname;
    const configValue = document.querySelector('#input').value;
    try {
        const response = await fetch('/api' + pathName, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: configValue
        });
        const data = await response.json();
        console.log('Success:', data);
        flashMessage('Save success', 'success');
    } catch (error) {
        console.error('Error:', error);
        flashMessage('Save failed due to error', 'danger');
    }
}

async function initialize_editor() {
    const configAndSchema = await getConfigAndSchema();
    const myschema = configAndSchema.schema;
    const myconfig = configAndSchema.config;
    const jsonEditorConfig = {
        use_name_attributes: false,
        iconlib: 'fontawesome5',
        theme: 'bootstrap4',
        show_opt_in: true,
        disable_edit_json: true,
        disable_properties: true,
        disable_collapse: false,
        enforce_const: true,
        startval: myconfig,
        schema: myschema
    };

    const editor = new JSONEditor(document.querySelector('#editor-container'), jsonEditorConfig);
    editor.on('change', function () {
        document.querySelector('#input').value = JSON.stringify(editor.getValue());
        document.querySelector('#get-params').textContent = JSON.stringify(editor.getValue(), null, 2);
    });
    editor.on('ready', function () {
        changeCheckboxStyle();
    });
    return editor;
}

const editor = initialize_editor();
{/* <label class="custom-control custom-checkbox" for=""><input type="checkbox" id="customCheck" class="custom-control-input"><label class="custom-control-label" for="customCheck">name</label>
</label> */}