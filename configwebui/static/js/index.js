'use strict';
let editor;
let editor_is_ready = false;
const statusIconDisappearDelay = 400;
const pageRefreshDelay = 400;

const pathName = window.location.pathname;
const pathNameParts = pathName.split('/').filter(part => part !== '');
const profile = pathNameParts[pathNameParts.length - 1];
const configRoot = pathNameParts[pathNameParts.length - 2];

const navbarCollapseElement = document.querySelector("#navbarNav");


const configSelectElement = document.getElementById('configSelect');
const profileSelectElement = document.getElementById('profileSelect');

const profileContainer = document.querySelector('#profile-container')
const profileManageElement = document.querySelector('#profile-manage')

const profileNameEditText = document.querySelector("#profile-name-edit")
const profileEditGroup = document.querySelector('#profile-edit-group')
const profileConfirmGroup = document.querySelector('#profile-confirm-group')

const profileAddButton = document.querySelector('#profile-add')
const profileRenameButton = document.querySelector('#profile-rename')
const profileDeleteButton = document.querySelector('#profile-delete')
const profileConfirmButton = document.querySelector('#profile-confirm')
const profileCancelButton = document.querySelector('#profile-cancel')

const editorLoadingIconElement = document.querySelector('#editor-loading-icon');
const editorLoadingIconElementBaseClassName = editorLoadingIconElement.className;

const mainProgramRunningIconElement = document.querySelector('#main-program-running-icon');
const mainProgramRunningIconElementBaseClassName = mainProgramRunningIconElement.className;

const jsonPreviewTextElement = document.querySelector('#json-preview-text');
const jsonPreviewTextElementBaseClassName = jsonPreviewTextElement.className;

const mainOutputTextElement = document.querySelector('#main-output-text');
const mainOutputTextElementBaseClassName = mainOutputTextElement.className;

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
        if (parent.classList.contains('editor-check') || parent.classList.contains('check-list')) {
            return;
        }

        input.className += ' form-check-input editor-check-input';
        if (parent.tagName.toLowerCase() === 'label') {
            input.className += ' form-check-input editor-check-input check-input-plain';
            parent.className = 'form-check editor-check';
            newLabel.className = 'form-check-label check-label-plain';
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'span') {
            input.className += ' form-check-input editor-check-input check-input-heading';
            parent.className = 'form-check editor-check d-inline-flex';
            newLabel.className = 'form-check-label check-label-heading';

            parent.childNodes.forEach(child => {
                if (child.nodeType === Node.TEXT_NODE && child.textContent.trim() !== '') {
                    newLabel.appendChild(child);
                }
            });
            parent.insertBefore(newLabel, input.nextSibling);
        } else if (parent.tagName.toLowerCase() === 'b') {
            input.className += ' form-check-input editor-check-input check-input-plain';
            parent.className = 'form-check editor-check user-add-item';
            newLabel.className = 'form-check-label check-label-plain';

            parent.insertBefore(newLabel, input.nextSibling);

            const newParent = document.createElement('label');
            while (parent.firstChild) {
                newParent.appendChild(parent.firstChild);
            }
            Array.from(parent.attributes).forEach(attr => {
                newParent.setAttribute(attr.name, attr.value);
            });
            parent.replaceWith(newParent);
        } else if (parent.tagName.toLowerCase() === 'div') {
            console.log(parent)
            parent.className += ' check-list'
            const formLabelElement = parent.querySelector('label[class="form-check-label"]')
            formLabelElement.textContent = formLabelElement.textContent.trim()

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
    const selectedValue = configSelectElement.value;
    if (selectedValue) {
        window.location.href = selectedValue;
    } else {
        window.location.href = '/';
    }
}

function navigateToProfile() {
    const selectedValue = profileSelectElement.value;
    if (selectedValue) {
        window.location.href = selectedValue;
    } else {
        window.location.href = '/';
    }
}

function collapseNavbar() {
    const bsCollapse = new bootstrap.Collapse(navbarCollapseElement, {
        toggle: false
    });
    bsCollapse.hide();
}

async function getConfigAndSchema() {
    let res = {};
    try {
        const response = await fetch('/api' + pathName, { method: 'GET' });
        const data = await response.json();
        res.config = data.config;
        res.schema = data.schema;
        if (data.success) {
            editorLoadingIconElement.className = editorLoadingIconElementBaseClassName + ' text-success';
        }
        else {
            editorLoadingIconElement.className = editorLoadingIconElementBaseClassName + ' text-danger';
            flashMessage('Failed to get config from server', 'danger');
        }
    }
    catch (error) {
        flashMessage('Failed to get config from server', 'danger');
        editorLoadingIconElement.className = editorLoadingIconElementBaseClassName + ' text-danger';
    }
    return res;
}

async function updateProfile(action, profileName) {
    clearFlashMessage();
    let method;
    let requestData = {};
    requestData.name = decodeURIComponent(profileName);
    if (action === 'update') {
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
        method = 'PATCH';
        const configValue = editor.getValue();
        requestData.config = configValue;
    } else if (action === 'add') {
        method = 'POST';
    } else if (action === 'rename') {
        method = 'PUT';
    } else if (action === 'delete') {
        method = 'DELETE';
    } else {
        return;
    }

    try {
        const response = await fetch(`/api${pathName}`, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
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
        flashMessage('Failed to update profile. Is the backend service working properly?', 'danger');
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
        flashMessage('Failed to launch the main program. Checkout your python backend.', 'danger');
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
    editorLoadingIconElement.className = editorLoadingIconElementBaseClassName + ' text-primary';
    editorLoadingIconElement.style.display = 'inline-block';
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
            jsonPreviewTextElement.value = JSON.stringify(editor.getValue(), null, 4);
        }
    });
    editor.on('ready', function () {
        editor_is_ready = true;
        setTimeout(() => changeStyle(), 0);
        setTimeout(() => {
            editorLoadingIconElement.style.display = 'none';
        }, statusIconDisappearDelay)
        jsonPreviewTextElement.wrap = "off";
    });
}

initialize_editor();

let currentProfileEditAction = ''
async function manage_profiles(action) {
    if (action === 'confirm') {
        let res;
        if (currentProfileEditAction === 'add') {
            res = await updateProfile('add', profileNameEditText.value);
            if (res) {
                setTimeout(() => {
                    window.location.href = `/config/${configRoot}/${profileNameEditText.value}`;
                }, pageRefreshDelay);
            }
        } else if (currentProfileEditAction === 'rename') {
            res = await updateProfile('rename', profileNameEditText.value);
            if (res) {
                setTimeout(() => {
                    window.location.href = `/config/${configRoot}/${profileNameEditText.value}`;
                }, pageRefreshDelay);
            }
        } else if (currentProfileEditAction === 'delete') {
            res = await updateProfile('delete', profile);
            if (res) {
                setTimeout(() => {
                    window.location.href = `/config/${configRoot}`;
                }, pageRefreshDelay);
            }
        }
        manage_profiles('cancel');

    } else if (action === 'cancel') {
        currentProfileEditAction = '';
        editor.enable();
        profileNameEditText.style.display = 'none';
        profileConfirmGroup.style.display = 'none';//隐藏确认按钮组
        profileEditGroup.style.removeProperty('display');//显示编辑按钮组
    } else {
        currentProfileEditAction = action;
        editor.disable();
        if (action !== 'delete') {
            profileNameEditText.style.removeProperty('display'); //显示文本框
            profileConfirmButton.className = 'btn btn-primary'
            profileCancelButton.className = 'btn btn-danger'
            if (action === 'add') {
                profileNameEditText.value = '';
            } else if (action === 'rename') {
                profileNameEditText.value = decodeURIComponent(profile);
            }
        } else {
            profileNameEditText.style.display = 'none';
            profileConfirmButton.className = 'btn btn-danger'
            profileCancelButton.className = 'btn btn-primary'
        }
        profileConfirmGroup.style.removeProperty('display');//显示确认按钮组
        profileEditGroup.style.display = 'none';//隐藏编辑按钮组
        profileConfirmButton.textContent = 'Confirm ' + action.charAt(0).toUpperCase() + action.slice(1);
    }
}

function get_output(func_type) {
    let complete = true;
    let outputTextElement;
    let outputTextElementBaseClassName;
    let runningIconElement;
    let runningIconElementBaseClassName;
    let url;
    let err_message;
    if (func_type === 'main') {
        outputTextElement = mainOutputTextElement;
        outputTextElementBaseClassName = mainOutputTextElementBaseClassName;
        runningIconElement = mainProgramRunningIconElement;
        runningIconElementBaseClassName = mainProgramRunningIconElementBaseClassName;
        url = `/api/get_main_output`;
        err_message = 'Failed to get output from the main program.';
    } else {
        return;
    }
    runningIconElement.className = runningIconElementBaseClassName + ' text-primary';
    runningIconElement.style.display = 'inline-block';
    outputTextElement.value = '';
    outputTextElement.className = outputTextElementBaseClassName;
    outputTextElement.scrollTop = outputTextElement.scrollHeight;
    const intervalId = setInterval(async () => {
        if (!complete) {
            return;
        }
        try {
            complete = false;
            const response = await fetch(url, {
                method: 'GET',
            });
            const data = await response.json();

            let scroll = false;
            if (outputTextElement.scrollTop + outputTextElement.clientHeight >= outputTextElement.scrollHeight - 10) {
                scroll = true;
            }
            outputTextElement.wrap = "off";
            outputTextElement.value += data.combined_output;
            if (data.has_warning) {
                runningIconElement.className = runningIconElementBaseClassName + ' text-warning';
                outputTextElement.className = outputTextElementBaseClassName + ' text-warning';
            }
            if (!data.running) {
                if (data.state) {
                    if (!data.has_warning) {
                        outputTextElement.className = outputTextElementBaseClassName + ' text-success';
                        runningIconElement.className = runningIconElementBaseClassName + ' text-success';
                    }
                } else {
                    outputTextElement.className = outputTextElementBaseClassName + ' text-danger';
                    runningIconElement.className = runningIconElementBaseClassName + ' text-danger';
                }
                for (const message of data.messages) {
                    outputTextElement.value += '\n' + message;
                }
                setTimeout(() => {
                    runningIconElement.style.display = 'none';
                }, statusIconDisappearDelay);
                clearInterval(intervalId);
            }
            if (scroll) {
                outputTextElement.scrollTop = outputTextElement.scrollHeight;
            }
        } catch (error) {
            outputTextElement.className = outputTextElementBaseClassName + ' text-danger';
            runningIconElement.className = runningIconElementBaseClassName + ' text-danger';
            flashMessage(err_message, 'danger');
            setTimeout(() => {
                runningIconElement.style.display = 'none';
            }, statusIconDisappearDelay);
            clearInterval(intervalId);
        }
        complete = true;
    }, 200);
}

const saveActionButtons = document.querySelectorAll('.save-action');
saveActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        await updateProfile('update', profile);
    });
});

const resetActionButtons = document.querySelectorAll('.reset-action');
resetActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        await reload();
    });
});

const launchActionButtons = document.querySelectorAll('.launch-action');
launchActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        if (await launch()) {
            get_output('main');
        }
    });
});

const terminateActionButtons = document.querySelectorAll('.terminate-action');
terminateActionButtons.forEach(button => {
    button.addEventListener('click', async () => {
        collapseNavbar();
        await terminate();
    });
});

profileAddButton.addEventListener('click', async () => {
    await manage_profiles('add')
});
profileRenameButton.addEventListener('click', async () => {
    await manage_profiles('rename')
});
profileDeleteButton.addEventListener('click', async () => {
    await manage_profiles('delete')
});
profileConfirmButton.addEventListener('click', async () => {
    await manage_profiles('confirm')
});
profileCancelButton.addEventListener('click', async () => {
    await manage_profiles('cancel')
});
document.addEventListener("click", async (event) => {
    if (!profileContainer.contains(event.target)) {
        await manage_profiles('cancel')
    }
});