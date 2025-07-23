import {Application as StimulusApp} from "Stimulus";

const Application = new StimulusApp();
/** @type {Promise<StimulusApp>} */
const applicationReady = Application.start().then(() => Application)
export {applicationReady}
