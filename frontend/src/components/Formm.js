import React, { useState } from "react";
import "./Form.css";

function Formm() {
  const [responses, setResponses] = useState({
    question1: "",
    question2: "",
    question3: "",
  });

  const handleChange = (e) => {
    setResponses({ ...responses, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log("Form responses:", responses);
    alert("Form submitted successfully!");
  };
  return (
    <div className="formm-container">
      <h2 className="kk">Answer and Check Symptoms</h2>
      <form onSubmit={handleSubmit}>
        <div className="question">
          <label>Do you like React?</label>
          <div className="options">
            <input type="radio" name="question1" value="Yes" onChange={handleChange} /> Yes
            <input type="radio" name="question1" value="No" onChange={handleChange} /> No
          </div>
        </div>
        <div className="question">
          <label>Have you used CSS before?</label>
          <div className="options">
            <input type="radio" name="question2" value="Yes" onChange={handleChange} /> Yes
            <input type="radio" name="question2" value="No" onChange={handleChange} /> No
          </div>
        </div>
        <div className="question">
          <label>Do you enjoy coding?</label>
          <div className="options">
            <input type="radio" name="question3" value="Yes" onChange={handleChange} /> Yes
            <input type="radio" name="question3" value="No" onChange={handleChange} /> No
          </div>
        </div>
        <button className="b22" type="submit">Submit</button>
      </form>
    </div>
  );
}

export default Formm;
