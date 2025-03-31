import { Link } from 'react-router-dom';
import skin from '../assets/skinvision.webp';
import car from '../assets/rash.png';
import Footer from './Footer';
import './Home.css';
function HomePage() {
  return (
    <div className='main'>
      <div className='bbox'>
        <div className='bbox-1'>
          <div>
            <img src={car} alt='' width='200' className='cart'></img>
          </div>
          <div>
            <h1 className='t1'>Say No to Skin Diseases!</h1>
            <p className='p11'>Check your skin on the smartphone and get instant results.*</p>
            <Link to="/upload"><button className="gradient-button">CHECK YOUR SKIN NOW</button></Link>
          </div>
          <div>
            <img src={skin} alt='' width='500' className='sk'></img>
          </div>
        </div>
        <p className='p12'>*The scan result is not a diagnosis. To obtain an accurate diagnosis and a recommendation for treatment - consult your doctor.</p>
      </div>
      
      <div>
        <h1 className='abc'>What do you know in Few Minutes?</h1>
        <p className='pa'>Risk Detection and Assessment of the 8 diseases as of now!</p>
      </div>

      <div className='infections'>
        <div className='fungal-infections'>
          <div>  
            <h2 className='pk'>FUNGAL INFECTIONS:</h2>
          </div>
          <div className="card1">
            <div className="first-content">
                <span>Athlete-foot</span>
            </div>
            <div className="second-content">
              <span className='ste'>Symptoms:</span>
              <p className='ert'>
                1.Itching <br />
                2.Cracks <br />
                3.Burning <br />
                4.Peeling-skin
              </p>
            </div>
          </div>
          <div className="card2">
            <div className="first-content">
                <span>Nail-Fungus</span>
            </div>
            <div className="second-content">
              <span className='ste'>Symptoms:</span>
              <p className='ert'>
                1.Thickened nails <br />
                2.Discoloration <br />
                3.Brittle nails <br />
                4.Bad odor
              </p>
            </div>
          </div>
          <div className="card3">
            <div className="first-content">
                <span>Ringworm</span>
            </div>
            <div className="second-content">
              <span className='ste'>Symptoms:</span>
              <p className='ert'>
                1.Red-shaped rash <br />
                2.Itching <br />
                3.Scaly skin <br />
                4.Inflammation
              </p>
            </div>
          </div>
        </div>

        <br/><hr/><br/>

        <div className='bacterial-infections'>
          <div>
            <h2 className='pk'>BACTERIAL INFECTIONS:</h2>
          </div>
          <div className="card1">
            <div className="first-content">
                <span>Cellulitis</span>
            </div>
            <div className="second-content">
              <span className='ste'>Symptoms:</span>
              <p className='ert'>
                1.Fever <br />
                2.Redness <br />
                3.Swelling <br />
                4.Warm skin
              </p>
            </div>
          </div>
          <div className="card2">
            <div className="first-content">
                <span>Impetigo</span>
            </div>
            <div className="second-content">
              <span className='ste'>Symptoms:</span>
              <p className='ert'>
                1.Sores <br />
                2.Blisters <br />
                3.Itching <br />
                4.Crusting
              </p>
            </div>
          </div>
        </div>

        <br/><hr/><br/>

        <div className='viral-infections'>
          <div>
            <h2 className='pk'>VIRAL INFECTIONS:</h2>
          </div>
          <div className="card1">
            <div className="first-content">
                <span>Chickenpox</span>
            </div>
            <div className="second-content">
              <span className='ste'>Symptoms:</span>
              <p className='ert'>
                1.Fever <br />
                2.Rashes <br />
                3.Fluid-filled blisters <br />
                4.Tiredness
              </p>
            </div>
          </div>
          <div className="card2">
            <div className="first-content">
                <span>Shingles</span>
            </div>
            <div className="second-content">
              <span className='ste'>Symptoms:</span>
              <p className='ert'>
                1.Burning pain <br />
                2.Rash <br />
                3.Blisters <br />
                4.Nerve pain
              </p>
            </div>
          </div>
        </div>

        <br/><hr/><br/>

        <div className='parasitic-infection'>
          <div>
            <h2 className='pk'>PARASITIC INFECTION:</h2>
          </div>
          <div className="card1">
            <div className="first-content">
                <span className='spa'>Cutaneous-larva-migrans</span>
            </div>
            <div className="second-content">
              <span className='ste'>Symptoms:</span>
              <p className='ert'>
                1.Red lines on skin <br />
                2.Rashes <br />
                3.Itching <br />
                4.Painful swelling
              </p>
            </div>
          </div>
        </div>
      </div>

      <Footer/>
    </div>
  );
}
export default HomePage;



// import React from 'react';
// import './Home.css';

// function Home() {
//   return (
//     <div className="home-container">
//       <h1 className="home-title">Welcome to Skin Disease Analyzer</h1>
//       <button className="home-button">Get Started</button>
//     </div>
//   );
// }

// export default Home;
