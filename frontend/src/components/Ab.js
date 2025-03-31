import './ab.css'
import rgt from '../assets/arrow_r_to_l.png'
import sim from '../assets/simp.png';
import ar from '../assets/arrow_l_to_r.png'
import acc from '../assets/access.png'

function Apage(){
    return(
        <div className='about-container'>
            <div className="title-div">
                <h1 id="title-text">ABOUT SKIN-NET ANALYZER :</h1>
            </div>
            <h1 id='h1'>Early Detection Saves Lives!</h1>
            <div>
                <p id='p'>Our Website helps in early detection, guiding users on whether to seek medical advice.</p>
                <p id='p'>This technology enhances easy accessibility to skin health monitoring with quick and reliable analysis.</p>
            </div>
            <h1 id='h2'>Why SkinNet Analyzer is worth using?</h1>
            <div className='sna-div'>
                <div className='sh1'>
                    <div className='sh1-image'>
                        <h2 className='hehe'>1. Simple to use</h2>
                        <div className='sh1-image2'>
                            <div className='sa'>
                                <img src={sim} alt='' width="150"></img>
                            </div>
                            <div className='arr'>
                                <img src={ar} alt='' width='100'></img>
                            </div>
                        </div>
                    </div>
                    <div className='sh1-content'>
                        <div className='circle-l'>
                            <div>
                                <p className='para'>Place your phone near rashes on</p>
                                <p className='para'>your skin or other formation and within</p>
                                <p className='para'>few minutes you will find out if there</p>   
                                <p className='para'>is cause for concern.</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div className='sh2'>
                    <div className='sh2-content'>
                        <div className='circle-r'>
                            <div>
                                <p className='para'>SkinNet is available anytime, anywhere.</p>
                                <p className='para'>Keep your health in check at your fingertips</p>
                                <p className='para'>even when you are on the go.</p>
                            </div>
                        </div>
                    </div>
                    <div className='sh2-image'>
                        <h2 className="jee">2. Easily accessible</h2>
                        <div className='sh2-image2'>
                            <div className='arc'>
                                <img src={rgt} alt='' width='100'></img>
                            </div>
                            <div className='pic1'>
                                <img src={acc} alt='' width='150'></img>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
export default Apage;