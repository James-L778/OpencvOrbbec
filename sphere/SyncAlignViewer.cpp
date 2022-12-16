#include "../window.hpp"

#include "libobsensor/hpp/Pipeline.hpp"
#include "libobsensor/hpp/Error.hpp"
#include <mutex>
#include <thread>

#define D 68
#define d 100
#define F 70
#define f 102
#define S 83
#define s 115
#define add 43
#define reduce 45
#define FEMTO 0x0635

static bool  sync    = false;
static bool  started = true;
static bool  hd2c    = false;
static bool  sd2c    = true;
static float alpha   = 0.5;
static int   _key    = -1;

const uint32_t colorWidth  = 640;
const uint32_t colorHeight = 480;
const uint32_t depthWidth  = 640;
const uint32_t depthHeight = 480;

std::mutex                    mutex_;
std::shared_ptr<ob::FrameSet> _frameSet;
bool                          _quit = false;


//保存深度图为png格式
void saveDepth(std::shared_ptr<ob::DepthFrame> depthFrame) {
    std::vector<int> compression_params;
    compression_params.push_back(cv::IMWRITE_PNG_COMPRESSION);
    compression_params.push_back(0);
    compression_params.push_back(cv::IMWRITE_PNG_STRATEGY);
    compression_params.push_back(cv::IMWRITE_PNG_STRATEGY_DEFAULT);
    std::string depthName = "depth.png";
    cv::Mat     depthMat(depthFrame->height(), depthFrame->width(), CV_16UC1, depthFrame->data());
    cv::imwrite(depthName, depthMat);
    std::cout << "Depth saved:" << depthName << std::endl;
}

//保存彩色图为png格式
void saveColor(std::shared_ptr<ob::ColorFrame> colorFrame) {
    std::vector<int> compression_params;
    compression_params.push_back(cv::IMWRITE_PNG_COMPRESSION);
    compression_params.push_back(0);
    compression_params.push_back(cv::IMWRITE_PNG_STRATEGY);
    compression_params.push_back(cv::IMWRITE_PNG_STRATEGY_DEFAULT);
    std::string colorName = "color.png";
    cv::Mat     colorRawMat(colorFrame->height(), colorFrame->width(), CV_8UC3, colorFrame->data());
    cv::imwrite(colorName, colorRawMat);
    std::cout << "Color saved:" << colorName << std::endl;
}


int main(int argc, char **argv) try {
    //创建一个Pipeline，Pipeline是整个高级API的入口，通过Pipeline可以很容易的打开和关闭
    //多种类型的流并获取一组帧数据
    ob::Pipeline pipe;

    //获取彩色相机的所有流配置，包括流的分辨率，帧率，以及帧的格式
    auto colorProfiles = pipe.getStreamProfileList(OB_SENSOR_COLOR);

    //通过接口设置感兴趣项，返回对应Profile列表的首个Profile
    auto colorProfile = colorProfiles->getVideoStreamProfile(colorWidth, colorHeight, OB_FORMAT_MJPG, 30);
    if(!colorProfile) {
        colorProfile = colorProfiles->getProfile(0)->as<ob::VideoStreamProfile>();
    }

    //获取深度相机的所有流配置，包括流的分辨率，帧率，以及帧的格式
    auto depthProfiles = pipe.getStreamProfileList(OB_SENSOR_DEPTH);

    //通过接口设置感兴趣项，返回对应Profile列表的首个Profile
    auto depthProfile = depthProfiles->getVideoStreamProfile(depthWidth, depthHeight, OB_FORMAT_Y16, 30);
    if(!depthProfile) {
        depthProfile = depthProfiles->getProfile(0)->as<ob::VideoStreamProfile>();
    }

    //通过创建Config来配置Pipeline要启用或者禁用哪些流，这里将启用彩色流和深度流
    std::shared_ptr<ob::Config> config = std::make_shared<ob::Config>();
    config->enableStream(colorProfile);
    config->enableStream(depthProfile);

    // 配置对齐模式为软件D2C对齐
    config->setAlignMode(ALIGN_D2C_SW_MODE);

    //启动在Config中配置的流，如果不传参数，将启动默认配置启动流
    pipe.start(config);

    //创建一个用于渲染的窗口，并设置窗口的分辨率
    Window app("SyncAlignViewer", colorProfile->width(), colorProfile->height());

    std::thread waitFrameThread([&]() {
        while(!_quit) {
            //以阻塞的方式等待一帧数据，该帧是一个复合帧，里面包含配置里启用的所有流的帧数据，
            //并设置帧的等待超时时间为100ms
            if(started) {
                auto frameSet = pipe.waitForFrames(100);
                if(frameSet == nullptr) {
                    continue;
                }
                std::unique_lock<std::mutex> lock(mutex_, std::defer_lock);
                if(lock.try_lock()) {
                    _frameSet = frameSet;
                }
            }
            else {
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
        }
    });

    while(app) {
        ////获取按键事件的键值
        int key = app.getKey();

        //按+键增加alpha
        if(_key != key && key == add) {
            alpha += 0.1f;
            if(alpha >= 1.0f) {
                alpha = 1.0f;
            }
        }

        //按-键减少alpha
        if(_key != key && key == reduce) {
            alpha -= 0.1f;
            if(alpha <= 0.0f) {
                alpha = 0.0f;
            }
        }
        //按D键开关硬件D2C
        if(_key != key && (key == D || key == d)) {
            try {
                if(!hd2c) {
                    started = false;
                    pipe.stop();
                    hd2c = true;
                    sd2c = false;
                    config->setAlignMode(ALIGN_D2C_HW_MODE);
                    pipe.start(config);
                    started = true;
                }
                else {
                    started = false;
                    pipe.stop();
                    hd2c = false;
                    sd2c = false;
                    config->setAlignMode(ALIGN_DISABLE);
                    pipe.start(config);
                    started = true;
                }
            }
            catch(std::exception &e) {
                std::cerr << "Property not support" << std::endl;
            }
        }

        //按S键开关软件D2C
        if(_key != key && (key == S || key == s)) {
            try {
                if(!sd2c) {
                    started = false;
                    pipe.stop();
                    sd2c = true;
                    hd2c = false;
                    config->setAlignMode(ALIGN_D2C_SW_MODE);
                    pipe.start(config);
                    started = true;
                }
                else {
                    started = false;
                    pipe.stop();
                    hd2c = false;
                    sd2c = false;
                    config->setAlignMode(ALIGN_DISABLE);
                    pipe.start(config);
                    started = true;
                }
            }
            catch(std::exception &e) {
                std::cerr << "Property not support" << std::endl;
            }
        }

        //按F键开关同步
        if(_key != key && (key == F || key == f)) {
            sync = !sync;
            if(sync) {
                try {
                    //开启同步功能
                    pipe.enableFrameSync();
                }
                catch(...) {
                    std::cerr << "Sync not support" << std::endl;
                }
            }
            else {
                try {
                    //关闭同步功能
                    pipe.disableFrameSync();
                }
                catch(...) {
                    std::cerr << "Sync not support" << std::endl;
                }
            }
        }

        _key = key;
        //创建格式转换Filter
        ob::FormatConvertFilter formatConverFilter;
        if(_frameSet != nullptr) {
            std::unique_lock<std::mutex> lock(mutex_);
            //在窗口中渲染一组帧数据，这里将渲染彩色帧及深度帧，RENDER_OVERLAY表示将彩色帧及
            //深度帧叠加显示
            auto colorFrame = _frameSet->colorFrame();
            
            auto depthFrame = _frameSet->depthFrame();
            
            if(colorFrame != nullptr && depthFrame != nullptr) {
                formatConverFilter.setFormatConvertType(FORMAT_MJPEG_TO_RGB888);
                colorFrame = formatConverFilter.process(colorFrame)->as<ob::ColorFrame>();
                formatConverFilter.setFormatConvertType(FORMAT_RGB888_TO_BGR);
                colorFrame = formatConverFilter.process(colorFrame)->as<ob::ColorFrame>();
                saveColor(colorFrame);
                saveDepth(depthFrame);
                app.render({ colorFrame, depthFrame }, alpha);
            }
            _frameSet = nullptr;
        }
        else {
            app.render({}, RENDER_SINGLE);
        }

        //清空帧缓冲队列，减少延时
        // while (pipe.waitForFrames(10) != nullptr) {};
    }

    _quit = true;
    waitFrameThread.join();

    //停止Pipeline，将不再产生帧数据
    pipe.stop();

    return 0;
}
catch(ob::Error &e) {
    std::cerr << "function:" << e.getName() << "\nargs:" << e.getArgs() << "\nmessage:" << e.getMessage() << "\ntype:" << e.getExceptionType() << std::endl;
    exit(EXIT_FAILURE);
}
